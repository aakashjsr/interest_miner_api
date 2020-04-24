import datetime
import monthdelta
from collections import OrderedDict
from rest_framework.views import APIView
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, DestroyAPIView, ListAPIView, RetrieveAPIView
from rest_framework.response import Response

from .serializers import PaperSerializer, ListDataSerializer, BlacklistedKeywordSerializer, ShortTermInterestSerializer, LongTermInterestSerializer
from .models import Keyword, BlacklistedKeyword, ShortTermInterest, Paper, Tweet, LongTermInterest, InterestTrend
from accounts.models import User
from .utils import get_interest_similarity_score

class LongTermInterestView(ListAPIView):
    serializer_class = LongTermInterestSerializer

    def get_queryset(self):
        order_key = "created_on" if self.request.GET.get("order") == "date" else "-weight"
        return self.request.user.long_term_interests.all().order_by(order_key)[:10]


class ShortTermInterestView(ListAPIView):
    serializer_class = ShortTermInterestSerializer

    def get_queryset(self):
        order_key = "created_on" if self.request.GET.get("order") == "date" else "-weight"
        return self.request.user.short_term_interests.all().order_by(order_key)[:10]


class ActivityStatsView(APIView):
    def get(self, request, *args, **kwargs):
        paper_data = OrderedDict()
        tweet_data = OrderedDict()

        for paper in Paper.objects.filter(user=request.user).order_by("year"):
            key_name = paper.year
            paper_data[key_name] = paper_data.get(key_name, 0) + 1

        for tweet in Tweet.objects.filter(user=request.user).order_by("created_at"):
            key_name = tweet.created_at.strftime("%B %Y")
            tweet_data[key_name] = tweet_data.get(key_name, 0) + 1
        return Response({"papers": paper_data, "tweets": tweet_data})


class PaperView(ListCreateAPIView):
    serializer_class = PaperSerializer

    def get_queryset(self):
        # return self.request.user.papers.filter(paper_id="manual")
        return self.request.user.papers.all()

    def post(self, request, *args, **kwargs):
        request_data = self.request.data
        request_data["user"] = request.user.id
        serializer = self.serializer_class(data=request_data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class PaperItemView(RetrieveUpdateDestroyAPIView):
    serializer_class = PaperSerializer

    def get_queryset(self):
        return self.request.user.papers.all()


class UserKeywordView(ListCreateAPIView):
    serializer_class = ShortTermInterestSerializer

    def get_queryset(self):
        return self.request.user.short_term_interests.filter(source=ShortTermInterest.MANUAL).order_by("keyword__name")

    def post(self, request, *args, **kwargs):
        serializer = ListDataSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        for keyword in serializer.validated_data["keywords"]:
            obj, _ = Keyword.objects.get_or_create(name=keyword)
            ShortTermInterest.objects.update_or_create(
                user=request.user, keyword=obj, source=ShortTermInterest.MANUAL
            )
        return Response({})

class UserBlacklistedKeywordView(ListCreateAPIView):
    serializer_class = BlacklistedKeywordSerializer

    def get_queryset(self):
        return self.request.user.blacklisted_keywords.all().order_by("keyword__name")

    def post(self, request, *args, **kwargs):
        serializer = ListDataSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        for keyword in serializer.validated_data["keywords"]:
            obj, _ = Keyword.objects.get_or_create(name=keyword)
            BlacklistedKeyword.objects.update_or_create(
                user=request.user, keyword=obj
            )
            ShortTermInterest.objects.filter(keyword=obj).delete()
            LongTermInterest.objects.filter(keyword=obj).delete()
        return Response({})


class UserBlacklistedKeywordItemView(DestroyAPIView):
    serializer_class = BlacklistedKeywordSerializer

    def get_queryset(self):
        return self.request.user.blacklisted_keywords.all().order_by("name")


class StreamGraphView(APIView):
    def get(self, request, *args, **kwargs):
        # get top 10 keywords
        today = datetime.date.today()
        response_data = {}
        for index in range(6):
            date = today - monthdelta.monthdelta(months=index)
            response_data[date.strftime("%B %Y")] = list(
                InterestTrend.objects.filter(month=date.month, year=date.year, user=request.user).order_by("-weight").values("keyword__name", "weight")[:10]
            )
        return Response(response_data)


class SimilarityView(RetrieveAPIView):
    def get_queryset(self):
        return User.objects.all()

    def get(self, request, *args, **kwargs):
        user = self.get_object()
        keywords_1 = list(user.long_term_interests.values_list("keyword__name", flat=True))
        keywords_2 = list(request.user.long_term_interests.values_list("keyword__name", flat=True))
        score = get_interest_similarity_score(keywords_1, keywords_2)
        return Response({"score": score})