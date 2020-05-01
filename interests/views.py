import datetime
import monthdelta
from collections import OrderedDict
from rest_framework.views import APIView
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, DestroyAPIView, ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import PaperSerializer, ListDataSerializer, BlacklistedKeywordSerializer, ShortTermInterestSerializer, LongTermInterestSerializer
from .models import Keyword, BlacklistedKeyword, ShortTermInterest, Paper, Tweet, LongTermInterest
from accounts.models import User
from .utils import get_interest_similarity_score

class LongTermInterestView(ListCreateAPIView):
    serializer_class = LongTermInterestSerializer

    def get_queryset(self):
        order_key = "created_on" if self.request.GET.get("order") == "date" else "-weight"
        return self.request.user.long_term_interests.all().order_by(order_key)

    def post(self, request, *args, **kwargs):
        serializer = ListDataSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        for keyword in serializer.validated_data["keywords"]:
            name, weight = keyword["name"], keyword["weight"]
            keyword_obj, created = Keyword.objects.get_or_create(name=name.lower())
            LongTermInterest.objects.update_or_create(
                user=request.user, keyword=keyword_obj, defaults={"weight": weight}
            )
        return Response({})


class LongTermInterestItemView(RetrieveUpdateDestroyAPIView):
    serializer_class = LongTermInterestSerializer

    def get_queryset(self):
        return self.request.user.long_term_interests.all()

    def delete(self, request, *args, **kwargs):
        item = self.get_object()
        BlacklistedKeyword.objects.update_or_create(user=request.user, keyword=item.keyword)
        ShortTermInterest.objects.filter(keyword=item.keyword, user=request.user).delete()
        LongTermInterest.objects.filter(keyword=item.keyword, user=request.user).delete()
        return Response({}, status=status.HTTP_204_NO_CONTENT)


class ShortTermInterestView(ListAPIView):
    serializer_class = ShortTermInterestSerializer

    def get_queryset(self):
        order_key = "created_on" if self.request.GET.get("order") == "date" else "-weight"
        today = datetime.date.today()
        return self.request.user.short_term_interests.filter(model_month=today.month, model_year=today.year).order_by(order_key)[:5]


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


class UserBlacklistedKeywordItemView(DestroyAPIView):
    serializer_class = BlacklistedKeywordSerializer

    def get_queryset(self):
        return self.request.user.blacklisted_keywords.all().order_by("name")


class StreamGraphView(APIView):
    def get(self, request, *args, **kwargs):
        # get top 10 keywords for twitter
        twitter_data = OrderedDict()
        scholar_data = OrderedDict()
        today = datetime.date.today()

        for index in range(5,-1,-1):
            # data for last 6 months
            date = today - monthdelta.monthdelta(months=index)
            twitter_data[date.strftime("%B %Y")] = list(
                ShortTermInterest.objects.filter(month=date.month, year=date.year, user=request.user, source=ShortTermInterest.TWITTER).order_by("-weight").values("keyword__name", "weight")[:10]
            )

        for index in range(4,-1,-1):
            # data for last 5 years
            year = today.year - index
            scholar_data[date.strftime("%Y")] = list(
                ShortTermInterest.objects.filter(year=year, user=request.user, source=ShortTermInterest.SCHOLAR).order_by("-weight").values("keyword__name", "weight")[:10]
            )
        response_data = {"twitter_data": twitter_data, "paper_data": scholar_data}
        return Response(response_data)


class SimilarityView(RetrieveAPIView):
    def get_queryset(self):
        return User.objects.all()

    def get(self, request, *args, **kwargs):
        user = self.get_object()
        keywords_1 = list(user.long_term_interests.values_list("keyword__name", flat=True))
        keywords_2 = list(request.user.long_term_interests.values_list("keyword__name", flat=True))
        score = 'N/A'
        if len(keywords_1) and len(keywords_2):
            score = get_interest_similarity_score(keywords_1, keywords_2)
            if score is None:
                score = 'N/A'
            else:
                score = round(float(score), 2)
        return Response({"score": score})
