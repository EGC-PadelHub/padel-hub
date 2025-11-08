import re

import unidecode
from sqlalchemy import any_, or_, and_

from app.modules.dataset.models import Author, DataSet, DSMetaData, PublicationType
from app.modules.featuremodel.models import FeatureModel, FMMetaData
from core.repositories.BaseRepository import BaseRepository


class ExploreRepository(BaseRepository):
    def __init__(self):
        super().__init__(DataSet)

    def filter(self, title="", sorting="newest", publication_type="any", tags=[], **kwargs):
        base_query =(
            self.model.query.join(DataSet.ds_meta_data)
            .join(DSMetaData.authors)
            .join(DataSet.feature_models, isouter=True)
            .join(FeatureModel.fm_meta_data, isouter=True)
            .filter(DSMetaData.dataset_doi.isnot(None))  
        )

        base_query = self._apply_title_filter(base_query, title)
        # base_query = self._apply_author_filter(base_query, kwargs.get("author", ""))
        # base_query = self._apply_description_filter(base_query, kwargs.get("description", ""))
        # base_query = self._apply_tags_filter(base_query, tags)
        # base_query = self._apply_publication_type_filter(base_query, publication_type)
        # base_query = self._apply_sorting(base_query, sorting)

        return base_query.all()


    def _apply_title_filter(self, query, title: str):
        if not title:
            return query
        
        normalized_query = unidecode.unidecode(title).lower()
        cleaned_query = re.sub(r'[,.":\'()\[\]^;!¡¿?]', "", normalized_query)
        title_filters = []
        for word in cleaned_query.split():
            title_filters.append(DSMetaData.title.ilike(f"%{word}%"))
        if not title_filters:
            return query
        return query.filter(and_(*title_filters))
    
    def _apply_author_filter(self, query, author: str):
        if not author:
            return query

        search_term = f"%{unidecode.unidecode(author).lower()}%"
        return query.filter(or_(
            Author.name.ilike(search_term),
            Author.affiliation.ilike(search_term),
            Author.orcid.ilike(search_term)
        ))
    
    def _apply_description_filter(self, query, description: str):
        if not description:
            return query

        normalized_query = unidecode.unidecode(description).lower()
        cleaned_query = re.sub(r'[,.":\'()\[\]^;!¡¿?]', "", normalized_query)
        description_filters = []
        for word in cleaned_query.split():
            description_filters.append(DSMetaData.description.ilike(f"%{word}%"))
        if not description_filters:
            return query
        return query.filter(or_(*description_filters))

    def _apply_tags_filter(self, query, tags: list):
        if not tags:
            return query

        for tag in tags:
            query = query.filter(DSMetaData.tags.ilike(f"%{tag}%"))
        return query

    def _apply_publication_type_filter(self, query, publication_type: str):
        if publication_type == "any" or not publication_type:
            return query

        matching_type = None
        for member in PublicationType:
            if member.value.lower() == publication_type:
                matching_type = member
                break

        if matching_type is not None:
            query = query.filter(DSMetaData.publication_type == matching_type.name)

        return query

    def _apply_sorting(self, query, sorting: str):
        if sorting == "oldest":
            query = query.order_by(self.model.created_at.asc())
        else:
            query = query.order_by(self.model.created_at.desc())
        return query
