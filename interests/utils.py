import datetime

from interests.models import Tweet, Paper, Keyword, ShortTermInterest, LongTermInterest, Category, BlacklistedKeyword
from interests.Keyword_Extractor.extractor import getKeyword
from interests.wikipedia_utils import wikicategory, wikifilter
from interests.update_interests import update_interest_models, normalize

from interests.Semantic_Similarity.Word_Embedding.IMsim import calculate_similarity


def generate_long_term_model(user_id):
    print("updating long term model for {}".format(user_id))
    short_term_model = ShortTermInterest.objects.filter(user_id=user_id, used_in_calc=False)
    short_term_data = {item.keyword.name: item.weight for item in short_term_model}
    long_term_data = {item.keyword.name: item.weight for item in LongTermInterest.objects.filter(user_id=user_id)}
    if not short_term_data:
        return
    new_data = update_interest_models(short_term_data, long_term_data)
    LongTermInterest.objects.filter(user_id=user_id).delete()
    short_term_model.update(used_in_calc=True)

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

        long_term_model = LongTermInterest.objects.create(**{"user_id": user_id, "keyword": keyword_instance, "weight": weight})
        tweet_list = [tweet for tweet in Tweet.objects.filter(user_id=user_id, full_text__icontains=keyword.lower())]
        paper_list = [paper for paper in Paper.objects.filter(user_id=user_id, abstract__icontains=keyword.lower())]
        if tweet_list:
            long_term_model.tweets.add(*tweet_list)
        if paper_list:
            long_term_model.papers.add(*paper_list)


def generate_short_term_model(user_id, source):
    blacklisted_keywords = list(
        BlacklistedKeyword.objects.filter(user_id=user_id).values_list("keyword__name", flat=True))

    if source == ShortTermInterest.TWITTER:
        for tweet in Tweet.objects.filter(user_id=user_id, used_in_calc=False):
            print(f"Extracting keywords from tweet id {tweet.id}")
            keywords = getKeyword(tweet.full_text or "", model="Yake", num=20)
            print(f"got keywords {keywords}")
            if not len(keywords.keys()):
                print("No keywords found")
                continue
            wiki_keyword_redirect_mapping, keyword_weight_mapping = wikifilter(keywords)
            print(keyword_weight_mapping)
            if not len(keyword_weight_mapping.keys()):
                print("No keywords found in weight mapping")
                continue
            keywords = normalize(keyword_weight_mapping)
            for keyword, weight in keywords.items():
                keyword = wiki_keyword_redirect_mapping.get(keyword, keyword)
                keyword = keyword.lower()
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

                s_interest, _ = ShortTermInterest.objects.update_or_create(
                    user_id=user_id, keyword=keyword_instance, model_month=tweet.created_at.month, model_year=tweet.created_at.year,
                    defaults={"source": source, "weight": weight})
                s_interest.tweets.add(tweet)
            tweet.used_in_calc = True
            tweet.save()


    if source == ShortTermInterest.SCHOLAR:
        for paper in Paper.objects.filter(user_id=user_id, used_in_calc=False):
            print(f"Extracting keywords from paper id {paper.id}")
            keywords = getKeyword(paper.abstract or "", model="SingleRank", num=20)
            print(f"got keywords {keywords}")
            if not len(keywords.keys()):
                print("No keywords found")
                continue

            wiki_keyword_redirect_mapping, keyword_weight_mapping = wikifilter(keywords)
            if not len(keyword_weight_mapping.keys()):
                print("No keywords found in weight mapping")
                continue
            keywords = normalize(keyword_weight_mapping)
            for keyword, weight in keywords.items():
                keyword = wiki_keyword_redirect_mapping.get(keyword, keyword)
                keyword = keyword.lower()
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

                s_interest, _ = ShortTermInterest.objects.update_or_create(
                    user_id=user_id, keyword=keyword_instance, model_month=1,
                    model_year=paper.year,
                    defaults={"source": source, "weight": weight})
                s_interest.papers.add(paper)

            paper.used_in_calc = True
            paper.save()

def get_interest_similarity_score(keyword_list_1, keyword_list_2):
    return calculate_similarity(keyword_list_1, keyword_list_2, embedding="Glove")
