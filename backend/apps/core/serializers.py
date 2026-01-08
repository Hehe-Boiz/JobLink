import urllib.parse
from rest_framework import serializers
class MediaURLSerializer(serializers.ModelSerializer):

    media_fields = []  # ví dụ: ["avatar"], ["cv"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        for f in getattr(self, "media_fields", []):
            val = getattr(instance, f, None)
            if val and hasattr(val, 'url'):
                data[f] = val.url
            else:
                if f == 'avatar':
                    data[f] = self.get_default_avatar(instance)
                else:
                    data[f] = ""

        return data

    def get_default_avatar(self, instance, name_field=None):
        name = ""
        if name_field and hasattr(instance, name_field):
            name = getattr(instance, name_field)
        elif hasattr(instance, 'first_name') and hasattr(instance, 'last_name'):
            name = f"{instance.last_name} {instance.first_name}".strip()
        if not name and hasattr(instance, 'username'):
            name = instance.username

        if not name:
            return ""

        encoded_name = urllib.parse.quote(name)
        return f"https://ui-avatars.com/api/?name={encoded_name}&background=random&color=fff&size=512&font-size=0.5"
