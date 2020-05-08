import datetime
import monthdelta
from collections import OrderedDict
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView
from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
    DestroyAPIView,
    ListAPIView,
    RetrieveAPIView,
)
from rest_framework.response import Response
from interests.Keyword_Extractor.extractor import getKeyword
from interests.wikipedia_utils import wikifilter
from interests.update_interests import normalize

from .serializers import (
    PaperSerializer,
    ListDataSerializer,
    BlacklistedKeywordSerializer,
    ShortTermInterestSerializer,
    LongTermInterestSerializer,
    InterestExtractionSerializer,
    KeywordSimilariySerializer,
)
from .models import (
    Keyword,
    BlacklistedKeyword,
    ShortTermInterest,
    Paper,
    Tweet,
    LongTermInterest,
)
from accounts.models import User
from .utils import get_interest_similarity_score


class LongTermInterestView(ListCreateAPIView):
    serializer_class = LongTermInterestSerializer

    def get_queryset(self):
        order_key = (
            "created_on" if self.request.GET.get("order") == "date" else "-weight"
        )
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

    def perform_destroy(self, instance):
        BlacklistedKeyword.objects.update_or_create(
            user=self.request.user, keyword=instance.keyword
        )
        ShortTermInterest.objects.filter(
            keyword=instance.keyword, user=self.request.user
        ).delete()
        return super().perform_destroy(instance)


class ShortTermInterestView(ListAPIView):
    serializer_class = ShortTermInterestSerializer

    def get_queryset(self):
        order_key = (
            "created_on" if self.request.GET.get("order") == "date" else "-weight"
        )
        today = datetime.date.today()
        return self.request.user.short_term_interests.filter(
            model_month=today.month, model_year=today.year
        ).order_by(order_key)[:5]


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

        top_twitter_keywords = list(
            ShortTermInterest.objects.filter(
                user=request.user, source=ShortTermInterest.TWITTER
            )
            .order_by("-weight")
            .values_list("keyword__name", flat=True)
        )
        top_twitter_keywords = list(set(top_twitter_keywords))[:10]

        top_paper_keywords = list(
            ShortTermInterest.objects.filter(
                user=request.user, source=ShortTermInterest.SCHOLAR
            )
            .order_by("-weight")
            .values_list("keyword__name", flat=True)
        )
        top_paper_keywords = list(set(top_paper_keywords))[:10]

        for index in range(5, -1, -1):
            # data for last 6 months
            date = today - monthdelta.monthdelta(months=index)
            twitter_data[date.strftime("%B %Y")] = list(
                ShortTermInterest.objects.filter(
                    model_month=date.month,
                    model_year=date.year,
                    user=request.user,
                    source=ShortTermInterest.TWITTER,
                    keyword__name__in=top_twitter_keywords,
                ).values("keyword__name", "weight")
            )

        for index in range(4, -1, -1):
            # data for last 5 years
            year = today.year - index
            scholar_data[str(year)] = list(
                ShortTermInterest.objects.filter(
                    model_year=year,
                    user=request.user,
                    source=ShortTermInterest.SCHOLAR,
                    keyword__name__in=top_paper_keywords,
                ).values("keyword__name", "weight")
            )
        response_data = {"twitter_data": twitter_data, "paper_data": scholar_data}
        return Response(response_data)


class SimilarityView(RetrieveAPIView):
    def get_queryset(self):
        return User.objects.all()

    def get(self, request, *args, **kwargs):
        user = self.get_object()
        keywords_1 = list(
            user.long_term_interests.values_list("keyword__name", flat=True)
        )
        keywords_2 = list(
            request.user.long_term_interests.values_list("keyword__name", flat=True)
        )
        score = 'N/A'
        if len(keywords_1) and len(keywords_2):
            score = get_interest_similarity_score(keywords_1, keywords_2)
            if score is None:
                score = 'N/A'
            else:
                score = round(float(score) * 100, 2)
        return Response({"score": score})


class PublicInterestExtractionView(GenericAPIView):
    """
    Extracts keywords from the specified text based on the selected algorithm
    """
    authentication_classes = ()
    permission_classes = ()
    serializer_class = InterestExtractionSerializer

    def post(self, request, *args, **kwargs):
        inputs = self.serializer_class(data=request.data)
        inputs.is_valid(raise_exception=True)
        payload = inputs.validated_data
        keyword_weight_mapping = getKeyword(
            payload["text"], model=payload["algorithm"], num=payload["num_of_keywords"]
        )
        if payload["wiki_filter"]:
            wiki_keyword_redirect_mapping, keyword_weight_mapping = wikifilter(
                keyword_weight_mapping
            )
        keywords = normalize(keyword_weight_mapping)
        return Response(keyword_weight_mapping)


class PublicKeywordSimilarityView(GenericAPIView):
    """
    Returns the similarity score for 2 sets of keywords based on the selected Algorithm
    """
    authentication_classes = ()
    permission_classes = ()
    serializer_class = KeywordSimilariySerializer

    def post(self, request, *args, **kwargs):
        inputs = self.serializer_class(data=request.data)
        inputs.is_valid(raise_exception=True)
        payload = inputs.validated_data
        score = get_interest_similarity_score(
            payload["keywords_1"], payload["keywords_2"], payload["algorithm"]
        )
        return Response({"score": round((score or 0) * 100, 2)})


class UserStreamGraphView(APIView):
    def get(self, request, *args, **kwargs):
        user = get_object_or_404(User, pk=kwargs["pk"])
        twitter_data = OrderedDict()
        scholar_data = OrderedDict()
        today = datetime.date.today()

        top_twitter_keywords = list(
            ShortTermInterest.objects.filter(
                user=user, source=ShortTermInterest.TWITTER
            )
            .order_by("-weight")
            .values_list("keyword__name", flat=True)
        )
        top_twitter_keywords = list(set(top_twitter_keywords))[:10]

        top_paper_keywords = list(
            ShortTermInterest.objects.filter(
                user=user, source=ShortTermInterest.SCHOLAR
            )
            .order_by("-weight")
            .values_list("keyword__name", flat=True)
        )
        top_paper_keywords = list(set(top_paper_keywords))[:10]

        for index in range(5, -1, -1):
            # data for last 6 months
            date = today - monthdelta.monthdelta(months=index)
            twitter_data[date.strftime("%B %Y")] = list(
                ShortTermInterest.objects.filter(
                    model_month=date.month,
                    model_year=date.year,
                    user=user,
                    source=ShortTermInterest.TWITTER,
                    keyword__name__in=top_twitter_keywords,
                ).values("keyword__name", "weight")
            )

        for index in range(4, -1, -1):
            # data for last 5 years
            year = today.year - index
            scholar_data[str(year)] = list(
                ShortTermInterest.objects.filter(
                    model_year=year,
                    user=user,
                    source=ShortTermInterest.SCHOLAR,
                    keyword__name__in=top_paper_keywords,
                ).values("keyword__name", "weight")
            )
        response_data = {"twitter_data": twitter_data, "paper_data": scholar_data}
        return Response(response_data)


class UserLongTermInterestView(ListAPIView):
    serializer_class = LongTermInterestSerializer

    def get_queryset(self):
        user = get_object_or_404(User, pk=self.kwargs["pk"])
        order_key = (
            "created_on" if self.request.GET.get("order") == "date" else "-weight"
        )
        return user.long_term_interests.all().order_by(order_key)


class UserShortTermInterestView(ListAPIView):
    serializer_class = ShortTermInterestSerializer

    def get_queryset(self):
        user = get_object_or_404(User, pk=self.kwargs["pk"])
        order_key = (
            "created_on" if self.request.GET.get("order") == "date" else "-weight"
        )
        today = datetime.date.today()
        return user.short_term_interests.filter(
            model_month=today.month, model_year=today.year
        ).order_by(order_key)[:5]


class UserActivityStatsView(APIView):
    def get(self, request, *args, **kwargs):
        paper_data = OrderedDict()
        tweet_data = OrderedDict()
        user = get_object_or_404(User, pk=kwargs["pk"])

        for paper in Paper.objects.filter(user=user).order_by("year"):
            key_name = paper.year
            paper_data[key_name] = paper_data.get(key_name, 0) + 1

        for tweet in Tweet.objects.filter(user=user).order_by("created_at"):
            key_name = tweet.created_at.strftime("%B %Y")
            tweet_data[key_name] = tweet_data.get(key_name, 0) + 1
        return Response({"papers": paper_data, "tweets": tweet_data})
