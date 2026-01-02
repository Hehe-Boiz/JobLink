from rest_framework import serializers


class MediaURLSerializer(serializers.ModelSerializer):

    media_fields = []  # ví dụ: ["avatar"], ["logo"]

    def to_representation(self, instance):
        data = super().to_representation(instance)

        for f in getattr(self, "media_fields", []):
            val = getattr(instance, f, None)
            # CloudinaryField & ImageField thường có .url
            data[f] = val.url if val else ""

        return data
