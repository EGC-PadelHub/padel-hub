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
        datasets = (
            self.model.query .join(DSMetaData, DataSet.ds_meta_data)
            .join(Author,DSMetaData.authors, isouter=True)
            .join(FeatureModel, DataSet.feature_models, isouter=True)
            .join(FMMetaData, FeatureModel.fm_meta_data, isouter=True)
            .filter(DSMetaData.dataset_doi.isnot(None))
        )

        datasets = self._apply_title_filter(datasets, title)
        datasets = self._apply_author_filter(datasets, kwargs.get("author", ""))
        # datasets = self._apply_description_filter(datasets, kwargs.get("description", ""))
        # datasets = self._apply_tags_filter(datasets, tags)
        # datasets = self._apply_publication_type_filter(datasets, publication_type)
        # datasets = self._apply_sorting(datasets, sorting)

        return datasets.distinct().all()

    def _apply_title_filter(self, query, title=""):
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
        
        # 1. Normalizamos y limpiamos la búsqueda, IGUAL QUE EL TÍTULO
        normalized_query = unidecode.unidecode(author).lower()
        cleaned_query = re.sub(r'[,.":\'()\[\]^;!¡¿?]', "", normalized_query)
        
        author_filters = []
        for word in cleaned_query.split():
            search_term = f"%{word}%"
            
            # 2. Creamos un OR para cada palabra (buscar en name O affiliation O orcid)
            word_filter = or_(
                Author.name.ilike(search_term),
                Author.affiliation.ilike(search_term),
                Author.orcid.ilike(search_term)
            )
            author_filters.append(word_filter)
        
        if not author_filters:
            return query
            
        # 3. Aplicamos un AND para todas las palabras
        # (Ej: si buscas "Javi Palla", busca "Javi" Y "Palla")
        return query.filter(and_(*author_filters))
    
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