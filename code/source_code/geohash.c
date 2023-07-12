#include <stdio.h>
#include <stdint.h>
#include <math.h>

#define HASHISZERO(r) (!(r).bits && !(r).step)
#define D_R (M_PI / 180.0)

const double EARTH_RADIUS_IN_METERS = 6372797.560856;    // Earth's quatratic mean radius for WGS-84

typedef struct {
    uint64_t bits;  // interleave64返回值
    uint8_t step;   // 0<step<=32
} GeoHashBits;

typedef struct {
    double min;
    double max;
} GeoHashRange;

typedef struct {
    GeoHashBits hash;
    GeoHashRange longitude;
    GeoHashRange latitude;
} GeoHashArea;

typedef struct {
    GeoHashBits north;
    GeoHashBits east;
    GeoHashBits west;
    GeoHashBits south;
    GeoHashBits north_east;
    GeoHashBits south_east;
    GeoHashBits north_west;
    GeoHashBits south_west;
} GeoHashNeighbors;

/**
 * Hashing works like this:
 * Divide the world into 4 buckets.  Label each one as such:
 *  -------------
 *  | 0,1 | 1,1 |
 *  -------------
 *  | 0,0 | 1,0 |
 *  -------------
所有未加static前缀的全局变量和函数都具有全局可见性,其它的源文件也能访问,访问前需通过extern关键字声明
静态函数和静态全局变量作用域仅限于所在的源文件,可以在不同的文件中定义同名函数和同名变量而不必担心命名冲突
静态局部变量只初始化一次,存放在静态存储区,所以它具备持久性和默认值0(全局变量也存储在静态数据区,在静态数据区内存中所有的字节默认值都是0x00)
同时编译多个文件方法:gcc file1.c file2.c -o run
*/

static inline uint64_t interleave64(uint32_t xlo, uint32_t ylo) {
    /*
    Interleave lower bits of x and y, so the bits of x are in the even positions and bits from y in the odd(奇数);
    x and y must initially be less than 2**32 (65536). From: https://graphics.stanford.edu/~seander/bithacks.html#InterleaveBMN
    */
    static const uint64_t B[] = {0x5555555555555555, 0x3333333333333333,0x0F0F0F0F0F0F0F0F, 0x00FF00FF00FF00FF,0x0000FFFF0000FFFF};
    static const unsigned int S[] = {1, 2, 4, 8, 16};
    uint64_t x = xlo;
    uint64_t y = ylo;

    x = (x | (x << S[4])) & B[4];
    y = (y | (y << S[4])) & B[4];

    x = (x | (x << S[3])) & B[3];
    y = (y | (y << S[3])) & B[3];

    x = (x | (x << S[2])) & B[2];
    y = (y | (y << S[2])) & B[2];

    x = (x | (x << S[1])) & B[1];
    y = (y | (y << S[1])) & B[1];

    x = (x | (x << S[0])) & B[0];
    y = (y | (y << S[0])) & B[0];

    return x | (y << 1);
}

static inline uint64_t deinterleave64(uint64_t interleaved) {
    static const uint64_t B[] = {0x5555555555555555, 0x3333333333333333,0x0F0F0F0F0F0F0F0F, 0x00FF00FF00FF00FF,0x0000FFFF0000FFFF, 0x00000000FFFFFFFF};
    static const unsigned int S[] = {0, 1, 2, 4, 8, 16};

    uint64_t x = interleaved;
    uint64_t y = interleaved >> 1;

    x = (x | (x >> S[0])) & B[0];
    y = (y | (y >> S[0])) & B[0];

    x = (x | (x >> S[1])) & B[1];
    y = (y | (y >> S[1])) & B[1];

    x = (x | (x >> S[2])) & B[2];
    y = (y | (y >> S[2])) & B[2];

    x = (x | (x >> S[3])) & B[3];
    y = (y | (y >> S[3])) & B[3];

    x = (x | (x >> S[4])) & B[4];
    y = (y | (y >> S[4])) & B[4];

    x = (x | (x >> S[5])) & B[5];
    y = (y | (y >> S[5])) & B[5];

    return x | (y << 32);
}

// inline只适合代码简单的函数,不能包含while、switch等复杂操作,并且内联函数本身不能是递归函数,如果函数体内的代码比较长,使用内联将导致内存消耗代价较高。
static inline double deg_rad(double ang) { return ang * D_R; }  // degree => radian
static inline double rad_deg(double ang) { return ang / D_R; }  // radian => degree

void geohashGetCoordRange(GeoHashRange *long_range, GeoHashRange *lat_range) {
    long_range->max = 180;
    long_range->min = -180;
    lat_range->max = 85.05112878;
    lat_range->min = -85.05112878;
}

int geohashEncode(const GeoHashRange *long_range, const GeoHashRange *lat_range,double longitude, double latitude, uint8_t step,GeoHashBits *hash) {
    if (hash == NULL || step > 32 || step == 0 || lat_range == NULL || long_range == NULL ||
        latitude < lat_range->min || latitude > lat_range->max || longitude < long_range->min || longitude > long_range->max
    ) return 0;

    hash->bits = 0;
    hash->step = step;
    double lat_offset =(latitude - lat_range->min) / (lat_range->max - lat_range->min);
    double long_offset =(longitude - long_range->min) / (long_range->max - long_range->min);
    lat_offset *= (1ULL << step); // 必须要加ULL,应为当step=31or32时符号位会变成负数or1直接溢出使结果变为0
    long_offset *= (1ULL << step);
    hash->bits = interleave64(lat_offset, long_offset);  // 隐式转换:double => uint32_t
    return 1;
}

int geohashEncodeWGS84(double longitude, double latitude, uint8_t step,GeoHashBits *hash) {
    GeoHashRange r[2] = {{0}};   // GeoHashRange r[2]={{.max=0,.min=1},{.min=2,.max=3}};
    geohashGetCoordRange(&r[0], &r[1]);
    return geohashEncode(&r[0], &r[1], longitude, latitude, step, hash);
}

int geohashDecode(const GeoHashRange long_range, const GeoHashRange lat_range,const GeoHashBits hash, GeoHashArea *area) {
    if (HASHISZERO(hash) || NULL == area || !long_range.max || !long_range.min || !lat_range.max || !lat_range.min)
        return 0;
    area->hash = hash;
    uint8_t step = hash.step;
    uint64_t hash_sep = deinterleave64(hash.bits); /* hash = [LAT][LONG] */

    double lat_scale = lat_range.max - lat_range.min;
    double long_scale = long_range.max - long_range.min;

    uint32_t ilato = hash_sep;       /* get lat part of deinterleaved hash */
    uint32_t ilono = hash_sep >> 32; /* shift over to get long part of hash */

    /* divide by 2**step.Then, for 0-1 coordinate, multiply times scale and add to the min to get the absolute coordinate. */
    area->latitude.min =lat_range.min + (ilato * 1.0 / (1ull << step)) * lat_scale;
    area->latitude.max =lat_range.min + ((ilato + 1) * 1.0 / (1ull << step)) * lat_scale;
    area->longitude.min =long_range.min + (ilono * 1.0 / (1ull << step)) * long_scale;
    area->longitude.max =long_range.min + ((ilono + 1) * 1.0 / (1ull << step)) * long_scale;
    return 1;
}

int geohashDecodeToLongLatWGS84(const GeoHashBits hash, double *xy) {
    GeoHashArea area = {{0}};
    GeoHashRange r[2] = {{0}};
    geohashGetCoordRange(&r[0], &r[1]);
    if (!xy || !geohashDecode(r[0], r[1], hash, &area))
        return 0;
    xy[0] = (area.longitude.min + area.longitude.max) / 2;
    xy[1] = (area.latitude.min + area.latitude.max) / 2;
    return 1;
}

static void geohash_move_x(GeoHashBits *hash, int8_t d) {  // 更改经度
    if (d == 0)
        return;
    uint64_t x;
    uint64_t y = hash->bits & 0x5555555555555555ULL;
    if (d > 0)
        x = (hash->bits | 0x5555555555555555ULL) + 1; // 使经度位二进制数加1(参考geohashEncode中的计算模型),超出长度step则x=0,相当于从180走到了-180
    else
        x = (hash->bits & 0xaaaaaaaaaaaaaaaaULL) - 1;
    x &= (0xaaaaaaaaaaaaaaaaULL >> (64 - hash->step * 2));
    hash->bits = (x | y);
}

static void geohash_move_y(GeoHashBits *hash, int8_t d) {
    if (d == 0)
        return;
    uint64_t x = hash->bits & 0xaaaaaaaaaaaaaaaaULL;
    uint64_t y ;
    if (d > 0)
        y = (hash->bits | 0xaaaaaaaaaaaaaaaaULL) + 1;
    else
        y = (hash->bits & 0x5555555555555555ULL) - 1;
    y &= (0x5555555555555555ULL >> (64 - hash->step * 2));
    hash->bits = (x | y);
}

void geohashNeighbors(const GeoHashBits *hash, GeoHashNeighbors *neighbors) {
    neighbors->east = *hash;    // 类型相同的结构体之间可以直接赋值
    neighbors->west = *hash;
    neighbors->north = *hash;
    neighbors->south = *hash;
    neighbors->south_east = *hash;
    neighbors->south_west = *hash;
    neighbors->north_east = *hash;
    neighbors->north_west = *hash;

    geohash_move_x(&neighbors->east, 1);  // -1,1是根据直角坐标系及方向共同确定
    geohash_move_x(&neighbors->west, -1);
    geohash_move_y(&neighbors->south, -1);
    geohash_move_y(&neighbors->north, 1);

    geohash_move_x(&neighbors->north_west, -1);
    geohash_move_y(&neighbors->north_west, 1);
    geohash_move_x(&neighbors->north_east, 1);
    geohash_move_y(&neighbors->north_east, 1);
    geohash_move_x(&neighbors->south_east, 1);
    geohash_move_y(&neighbors->south_east, -1);
    geohash_move_x(&neighbors->south_west, -1);
    geohash_move_y(&neighbors->south_west, -1);
}

double geohashGetDistance(double lon1d, double lat1d, double lon2d, double lat2d) {
    double lat1r, lon1r, lat2r, lon2r, u, v;
    lat1r = deg_rad(lat1d);
    lon1r = deg_rad(lon1d);
    lat2r = deg_rad(lat2d);
    lon2r = deg_rad(lon2d);
    u = sin((lat2r - lat1r) / 2);  // 三角函数参数是弧度而非角度
    v = sin((lon2r - lon1r) / 2);
    return 2.0 * EARTH_RADIUS_IN_METERS * asin(sqrt(u * u + cos(lat1r) * cos(lat2r) * v * v));
}

int main(){
    uint32_t x=0;
    uint32_t y=0b11111111111111111111111111111111;
    printf("%llu\n",deinterleave64(interleave64(x, y)));

    GeoHashBits hash={ .bits=1234567,.step=20};
    GeoHashNeighbors neighbors;
    geohashNeighbors(&hash,&neighbors);
}

/* GEOHASH key ele1 ele2 ... eleN
 * Returns an array with an 11 characters geohash representation of the position of the specified elements.
 */
void geohashCommand(client *c) {
    char *geoalphabet= "0123456789bcdefghjkmnpqrstuvwxyz";
    int j;

    /* Look up the requested zset */
    robj *zobj = lookupKeyRead(c->db, c->argv[1]);
    if (checkType(c, zobj, OBJ_ZSET)) return;

    /* Geohash elements one after the other, using a null bulk reply for missing elements. */
    addReplyArrayLen(c,c->argc-2);
    for (j = 2; j < c->argc; j++) {
        double score;
        if (!zobj || zsetScore(zobj, c->argv[j]->ptr, &score) == C_ERR) {
            addReplyNull(c);
        } else {
            /* The internal format we use for geocoding is a bit different
             * than the standard, since we use as initial latitude range
             * -85,85, while the normal geohashing algorithm uses -90,90.
             * So we have to decode our position and re-encode using the
             * standard ranges in order to output a valid geohash string. */

            /* Decode... */
            double xy[2];
            if (!decodeGeohash(score,xy)) {
                addReplyNull(c);
                continue;
            }

            /* Re-encode */
            GeoHashRange r[2];
            GeoHashBits hash;
            r[0].min = -180;
            r[0].max = 180;
            r[1].min = -90;
            r[1].max = 90;
            geohashEncode(&r[0],&r[1],xy[0],xy[1],26,&hash);

            char buf[12];
            int i;
            for (i = 0; i < 11; i++) {
                int idx;
                if (i == 10) {
                    /* We have just 52 bits, but the API used to output
                     * an 11 bytes geohash. For compatibility we assume
                     * zero. */
                    idx = 0;
                } else {
                    idx = (hash.bits >> (52-((i+1)*5))) & 0x1f;
                }
                buf[i] = geoalphabet[idx];
            }
            buf[11] = '\0';
            addReplyBulkCBuffer(c,buf,11);
        }
    }
}
