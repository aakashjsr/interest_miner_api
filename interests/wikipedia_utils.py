import wikipediaapi

import wikipediaapi
import requests
import json
from pattern.text.en import singularize


def wikifilter(keyword):
    wiki_wiki = wikipediaapi.Wikipedia('en')
    candidate = {}
    final = {}
    redirect = {}
    relation = {}
    
    
    for key in keyword.keys():
        page_py = wiki_wiki.page(key)
        if page_py.exists() == True:
            query = requests.get(r'https://en.wikipedia.org/w/api.php?action=query&titles={}&&redirects&format=json'.format(key))
            data = json.loads(query.text)
            PAGES = data["query"]["pages"]
            #print(PAGES)
            for v in PAGES.values():
                redirect[key]= v["title"]
                #print(redirect)
                temp_list = relation.get(v["title"], [])
                temp_list.append(key)
                relation[v["title"]] = temp_list
                #print(relation)
                final[v["title"]]=0  
            
        elif page_py.exists() == False:
            singles = singularize(key)
            page_py = wiki_wiki.page(singles)
            if page_py.exists() == True:
                query = requests.get(r'https://en.wikipedia.org/w/api.php?action=query&titles={}&&redirects&format=json'.format(singles))
                data = json.loads(query.text)
                PAGES = data["query"]["pages"]
                #print(PAGES)
                for v in PAGES.values():
                    redirect[key]= v["title"]
                    #print(redirect)
                    temp_list = relation.get(v["title"], [])
                    temp_list.append(key)
                    relation[v["title"]] = temp_list
                   # print(relation)
                    final[v["title"]]=0

    for k in redirect.keys():
        final[redirect[k]]=  final[redirect[k]]+keyword[k]
#     print(final)
    
    
    return relation, final

def wikicategory(interest):
    symbols = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '(', ')', ',']
    stoplist = ['of', 'by', 'lists', 'from', 'articles', 'terms']
    wiki = wikipediaapi.Wikipedia('en')
    categorie = []
    noise = []
    l = wiki.page(interest)
    a = wiki.categories(l, clshow='!hidden')

    for k in a.keys():
        cat = k.replace("Category:", "")
        if len(cat.split()) <= 4 and cat != 'Disambiguation pages':
            categorie.append(cat)

    for s in symbols:
        for c in categorie:
            if s in c.lower():
                noise.append(c)

    for c in categorie:
        for s in stoplist:
            if s in c.lower().split():
                noise.append(c)

    noise = list(set(noise))

    for n in noise:
        categorie.remove(n)

    return categorie
