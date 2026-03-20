from elasticsearch import Elasticsearch
from flask import current_app

INDEX_NAME = 'nyumbalink_properties'


def get_es():
    return Elasticsearch(current_app.config['ELASTICSEARCH_URL'])


def create_index():
    es = get_es()
    if not es.indices.exists(index=INDEX_NAME):
        es.indices.create(index=INDEX_NAME, body={
            'mappings': {
                'properties': {
                    'title': {'type': 'text', 'analyzer': 'standard'},
                    'description': {'type': 'text'},
                    'location': {'type': 'text'},
                    'county': {'type': 'keyword'},
                    'town': {'type': 'keyword'},
                    'category': {'type': 'keyword'},
                    'price': {'type': 'float'},
                    'bedrooms': {'type': 'integer'},
                    'bathrooms': {'type': 'integer'},
                    'plot_size': {'type': 'float'},
                    'verification_status': {'type': 'keyword'},
                    'status': {'type': 'keyword'},
                    'coords': {'type': 'geo_point'},
                    'created_at': {'type': 'date'},
                }
            }
        })


def index_property(prop):
    es = get_es()
    doc = {
        'id': prop.id,
        'title': prop.title,
        'description': prop.description or '',
        'location': prop.location,
        'county': prop.county,
        'town': prop.town,
        'category': prop.category,
        'price': float(prop.price) if prop.price else 0,
        'bedrooms': prop.bedrooms,
        'bathrooms': prop.bathrooms,
        'plot_size': float(prop.plot_size) if prop.plot_size else None,
        'verification_status': prop.verification_status,
        'status': prop.status,
        'created_at': prop.created_at.isoformat() if prop.created_at else None,
    }
    if prop.latitude and prop.longitude:
        doc['coords'] = {'lat': float(prop.latitude), 'lon': float(prop.longitude)}

    es.index(index=INDEX_NAME, id=prop.id, body=doc)


def delete_property_index(property_id: str):
    es = get_es()
    try:
        es.delete(index=INDEX_NAME, id=property_id)
    except Exception:
        pass


def search_properties(query: str, filters: dict = None, page: int = 1, per_page: int = 12) -> dict:
    es = get_es()
    filters = filters or {}

    must = []
    if query:
        must.append({
            'multi_match': {
                'query': query,
                'fields': ['title^3', 'description', 'location^2', 'county', 'town^2'],
                'fuzziness': 'AUTO',
            }
        })

    filter_clauses = [
        {'term': {'verification_status': 'verified'}},
        {'term': {'status': 'active'}},
    ]

    if filters.get('category'):
        filter_clauses.append({'term': {'category': filters['category']}})
    if filters.get('county'):
        filter_clauses.append({'term': {'county': filters['county']}})
    if filters.get('min_price') or filters.get('max_price'):
        price_range = {}
        if filters.get('min_price'):
            price_range['gte'] = filters['min_price']
        if filters.get('max_price'):
            price_range['lte'] = filters['max_price']
        filter_clauses.append({'range': {'price': price_range}})
    if filters.get('bedrooms'):
        filter_clauses.append({'range': {'bedrooms': {'gte': filters['bedrooms']}}})

    body = {
        'query': {
            'bool': {
                'must': must if must else [{'match_all': {}}],
                'filter': filter_clauses,
            }
        },
        'from': (page - 1) * per_page,
        'size': per_page,
        'sort': [{'_score': 'desc'}, {'created_at': 'desc'}],
    }

    result = es.search(index=INDEX_NAME, body=body)
    hits = result['hits']
    return {
        'ids': [hit['_id'] for hit in hits['hits']],
        'total': hits['total']['value'],
    }
