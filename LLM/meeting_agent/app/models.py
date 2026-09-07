from tortoise import fields, models

class User(models.Model):
    id = fields.IntField(pk=True)
    username = fields.CharField(max_length=50, unique=True, description="用户名，唯一")
    password_hash = fields.CharField(max_length=128, description="bcrypt哈希密码")

    class Meta:
        table = "users"
