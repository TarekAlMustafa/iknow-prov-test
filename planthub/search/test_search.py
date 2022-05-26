from __future__ import print_function, unicode_literals

# Test script for Search as you type
from elasticsearch_dsl import (
    Completion,
    Document,
    Keyword,
    Nested,
    SearchAsYouType,
    connections,
)
from elasticsearch_dsl.query import MultiMatch


class Person(Document):
    name = SearchAsYouType(max_shingle_size=3)
    test = Completion()
    test2 = Keyword()
    translation = Nested(
        multi=True,
        properties={
            'name': Completion(),
            'lang': Keyword(),
        }
    )

    class Index:
        name = 'test-search-as-you-type'
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0
        }


if __name__ == '__main__':
    # initiate the default connection to elasticsearch
    connections.create_connection()

    # create the empty index
    Person.init()

    import pprint

    pprint.pprint(Person().to_dict(), indent=2)

    # index some sample data
    names = [
        'Andy Warhol',
        'Alphonse Mucha',
        'Henri de Toulouse-Lautrec',
        'Jára Cimrman',
    ]
    for id, name in enumerate(names):
        Person(_id=id, name=name).save()

    # refresh index manually to make changes live
    Person._index.refresh()
    print(Person._index.get_mapping())
    # run some suggestions
    for text in ('já', 'Cimr', 'toulouse', 'Henri Tou', 'a'):
        s = Person.search()

        s.query = MultiMatch(
            query=text,
            type="bool_prefix",
            fields=[
                "name",
                "name._2gram",
                "name._3gram"
            ]
        )

        response = s.execute()

        # print out all the options we got
        for h in response:
            print('%15s: %25s' % (text, h.name))
