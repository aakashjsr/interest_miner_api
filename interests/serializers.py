from .models import Paper, Keyword, BlacklistedKeyword, ShortTermInterest, LongTermInterest, Category
from rest_framework import serializers


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("name", )


class PaperSerializer(serializers.ModelSerializer):
    class Meta:
        model = Paper
        fields = "__all__"


class KeywordSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True)

    class Meta:
        model = Keyword
        fields = "__all__"


class BlacklistedKeywordSerializer(serializers.ModelSerializer):
    keyword = serializers.SerializerMethodField()

    def get_keyword(self, instance):
        return instance.keyword.name

    class Meta:
        model = BlacklistedKeyword
        fields = "__all__"

class ShortTermInterestSerializer(serializers.ModelSerializer):
    keyword = serializers.SerializerMethodField()
    categories = serializers.SerializerMethodField()
    paper_db_ids = serializers.SerializerMethodField()
    tweet_ids = serializers.SerializerMethodField()

    def get_tweet_ids(self, instance):
        if instance.tweets.count():
            return [tweet.id_str for tweet in instance.tweets.all()]
        return []

    def get_paper_db_ids(self, instance):
        return list(instance.papers.values_list("id", flat=True))

    def get_categories(self, instance):
        return CategorySerializer(instance.keyword.categories.all(), many=True).data

    def get_keyword(self, instance):
        return instance.keyword.name

    class Meta:
        model = ShortTermInterest
        fields = "__all__"


class LongTermInterestSerializer(serializers.ModelSerializer):
    keyword = serializers.SerializerMethodField()
    categories = serializers.SerializerMethodField()
    tweet_ids = serializers.SerializerMethodField()
    papers = PaperSerializer(many=True)
    

    def get_tweet_ids(self, instance):
        if instance.tweets.count():
            return [tweet.id_str for tweet in instance.tweets.all()]
        return []

    def get_categories(self, instance):
        return CategorySerializer(instance.keyword.categories.all(), many=True).data

    def get_keyword(self, instance):
        return instance.keyword.name

    class Meta:
        model = LongTermInterest
        fields = "__all__"


class ListDataSerializer(serializers.Serializer):
    keywords = serializers.ListField(required=True)
