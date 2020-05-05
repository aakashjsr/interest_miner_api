import requests
from retrying import retry
from langdetect import detect


class SemanticScholarAPI:
    def __init__(self):
        self.API_URL = 'http://api.semanticscholar.org/v1'

    def paper(self, id, include_unknown_references=False) -> dict:
        '''Paper lookup

        :param id: S2PaperId, DOI or ArXivId.
        :param include_unknown_references : bool, (optional) include non referenced paper.
        :returns: paper data or empty :class:`dict` if not found.
        :rtype: :class:`dict`
        '''

        data = self.__get_data('paper', id, include_unknown_references)

        return data

    def author(self, id) -> dict:
        '''Author lookup

        :param id: S2AuthorId.
        :returns: author data or empty :class:`dict` if not found.
        :rtype: :class:`dict`
        '''

        data = self.__get_data('author', id)

        return data

    def __get_data(self, method, id, include_unknown_references=False) -> dict:
        '''Get data from Semantic Scholar API

        :param method: 'paper' or 'author'.
        :param id: :class:`str`.
        :returns: data or empty :class:`dict` if not found.
        :rtype: :class:`dict`
        '''

        data = {}
        print("Getting {}".format(method))
        method_types = ['paper', 'author']
        if method not in method_types:
            raise ValueError(
                'Invalid method type. Expected one of: {}'.format(method_types)
            )

        url = '{}/{}/{}'.format(self.API_URL, method, id)
        if include_unknown_references:
            url += '?include_unknown_references=true'
        print("making request")
        r = requests.get(url)
        print("response received")

        if r.status_code == 200:
            data = r.json()
            if len(data) == 1 and 'error' in data:
                data = {}
        elif r.status_code == 429:
            raise ConnectionRefusedError('HTTP status 429 Too Many Requests.')

        return data

    def get_paper(self, author_id, year):
        author = self.author(author_id)
        paper = author["papers"]
        collected_papers = []
        for p in paper:
            if p["year"] == year:
                a = self.paper(p["paperId"])["abstract"]
                #             print(a)
                try:
                    lan = detect(a)
                    #                 print(lan)
                    if lan == 'en':
                        p["abstract"] = a
                        collected_papers.append(p)
                except TypeError:
                    collected_papers.append(p)
        print(collected_papers)
        return collected_papers

    def get_user_papers(self, user, start_year, end_year):
        if not user.author_id:
            print("No Author id present for user {}".format(user.author_id))
            return
        author = self.author(user.author_id)
        papers = author["papers"]
        collectedpapers = []
        for paper in papers:
            if start_year <= paper["year"] <= end_year:
                abstract = self.paper(paper["paperId"])["abstract"]
                try:
                    lan = detect(abstract)
                    if lan == 'en':
                        paper["abstract"] = abstract
                        collectedpapers.append(paper)
                except TypeError:
                    collectedpapers.append(paper)
        return collectedpapers


# a=ob.get_paper(1724546, 2018, 2019)
