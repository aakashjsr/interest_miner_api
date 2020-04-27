import datetime

from interests.models import Tweet, Paper, Keyword, ShortTermInterest, LongTermInterest, Category, BlacklistedKeyword, InterestTrend
from interests.Keyword_Extractor.extractor import getKeyword
from interests.wikipedia_utils import wikicategory, wikifilter
from interests.update_interests import update_interest_models

from interests.Semantic_Similarity.Word_Embedding.IMsim import calculate_similarity


def generate_long_term_model(user_id):
    print("updating long term model for {}".format(user_id))
    keyword_source_map = {item.keyword.name: item.source for item in ShortTermInterest.objects.filter(user_id=user_id)}
    short_term_data = {item.keyword.name: item.weight for item in ShortTermInterest.objects.filter(user_id=user_id)}
    long_term_data = {item.keyword.name: item.weight for item in LongTermInterest.objects.filter(user_id=user_id)}
    if not short_term_data:
        return
    new_data = update_interest_models(short_term_data, long_term_data)
    LongTermInterest.objects.filter(user_id=user_id).delete()

    for keyword, weight in new_data.items():
        print(keyword, weight)
        keyword_instance, created = Keyword.objects.get_or_create(name=keyword.lower())
        if created:
            print("getting wiki categories")
            categories = wikicategory(keyword)
            for category in categories:
                category_instance, _ = Category.objects.get_or_create(name=category)
                keyword_instance.categories.add(category_instance)
            keyword_instance.save()
        else:
            print("Keyword found in db")
        print("keyword obtained")

        source = keyword_source_map.get(keyword, "")
        attrs = {"source": source, "user_id": user_id, "keyword": keyword_instance, "weight": weight}

        if source == ShortTermInterest.TWITTER:
            attrs["tweet"] = Tweet.objects.filter(full_text__icontains=keyword).order_by("-created_at").first()
        elif source == ShortTermInterest.SCHOLAR:
            attrs["paper"] = Paper.objects.filter(abstract__icontains=keyword).order_by("-created_on").first()

        LongTermInterest.objects.create(**attrs)


def generate_short_term_model(user_id, source):
    keywords = {}
    extraction_model = "Yake" if source == ShortTermInterest.TWITTER else "SingleRank"
    cls = Tweet if source == ShortTermInterest.TWITTER else Paper
    text_attribute = "full_text" if source == ShortTermInterest.TWITTER else "abstract"
    blacklisted_keywords = list(
        BlacklistedKeyword.objects.filter(user_id=user_id).values_list("keyword__name", flat=True))

    print("Generating short term model from {}".format(source))
    for item in cls.objects.filter(user_id=user_id, used_in_calc=False):
        keywords.update(getKeyword(getattr(item, text_attribute) or "", model=extraction_model, num=20))
        item.used_in_calc = True
        item.save()

    print("Found {} keyword".format(len(keywords.keys())))
    print("Applying wiki filter")
    keywords = wikifilter(keywords)[1]
    print("Filtered down keyword to {}".format(len(keywords.keys())))
    for keyword, weight in keywords.items():
        keyword = keyword.lower()
        print(keyword, weight)
        if keyword in blacklisted_keywords:
            print("Skipping {} as its blacklisted".format(keyword))
            continue
        keyword_instance, created = Keyword.objects.get_or_create(name=keyword.lower())
        if created:
            print("getting wiki categories")
            categories = wikicategory(keyword)
            for category in categories:
                category_instance, _ = Category.objects.get_or_create(name=category)
                keyword_instance.categories.add(category_instance)
            keyword_instance.save()
        else:
            print("Keyword found in db")
        print("keyword obtained")
        defaults = {"source": source, "weight": weight}
        if source == ShortTermInterest.TWITTER:
            defaults["tweet"] = Tweet.objects.filter(full_text__icontains=keyword).order_by("-created_at").first()
        elif source == ShortTermInterest.SCHOLAR:
            defaults["paper"] = Paper.objects.filter(abstract__icontains=keyword).order_by("-created_on").first()
        ShortTermInterest.objects.update_or_create(user_id=user_id, keyword=keyword_instance, defaults=defaults)


def capture_interest_trend(user_id):
    today = datetime.date.today()
    for item in LongTermInterest.objects.filter(user_id=user_id):
        InterestTrend.objects.update_or_create(
            user_id=user_id, keyword=item.keyword, month=today.month, year=today.year, defaults={"weight": item.weight}
        )


def get_interest_similarity_score(keyword_list_1, keyword_list_2):
    return calculate_similarity(keyword_list_1, keyword_list_2, embedding="Glove")
