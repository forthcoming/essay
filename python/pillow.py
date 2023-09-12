from PIL import Image, ImageFilter, ImageEnhance, ImageDraw, ImageFont

im = Image.open('C:/Users/root/Desktop/22.jpg')  # 手动更改后缀并不能改变其照片格式
im.save('test.png')  # 转换图像格式
new_img = im.copy()
new_img.show()
im2 = im.filter(ImageFilter.BLUR)  # 图像模糊化

im.thumbnail((200, 200))  # 会维持原来的比例不变
im.save('nail.jpg')
print(im.format, im.size, im.mode, im.width, im.height)

region = im.crop(
    (100, 100, 300, 300))  # The box is a 4-tuple defining the left, upper, right, and lower pixel coordinate.
region = region.transpose(Image.ROTATE_90)
im.paste(region, (200, 200, 400, 400))  # 尺寸必须与region大小完全一致

im.rotate(45).save('rotate.jpg')
im.resize((500, 500)).show()  # 不会维持比例,会以给定的比例伸缩图片
im.convert('L')  # 返回一个新的im对象

r, g, b = im.split()
im = Image.merge("RGB", (r, g, b))
out = im.point(lambda i: i * 2.2)
out.show()

draw = ImageDraw.Draw(im)
font = ImageFont.truetype('arial.ttf', 40)
color = (255, 0, 0)
draw.text((20, 20), '1234', color, font=font)
im.show()

contrast = ImageEnhance.Contrast(im)  # 对比度增强
im = contrast.enhance(50)  # 其实已二值化
brightness = ImageEnhance.Brightness(im)
im = brightness.enhance(80)  # 亮度增强
sharpness = ImageEnhance.Sharpness(im)
im = sharpness.enhance(80)  # 锐度增强
color = [(index, i) for index, i in enumerate(im.histogram())]
color.sort(key=lambda x: x[1], reverse=True)
print(color)

# a,b等价
pix = im.load()
a = [i for i in im.getdata()]
b = [pix[j, i] for i in range(im.height) for j in range(im.width)]
