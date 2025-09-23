from typing import Any, Dict, Optional
import time
from .protocol import Metric

class DatasetQualityMetric(Metric):
    
    def __init__(self) -> None:
        self.dataset_quality: float = 0.0
        self.dataset_quality_latency: float = 0.0
    
    def get_example_count(self, parsed_data: Dict[str, Any]) -> int:
        """Get number of examples/samples in dataset"""
        if parsed_data.get('category') == 'DATASET':
            card_data = parsed_data.get('cardData', {})
            dataset_info = card_data.get('dataset_info', {})
            
            if isinstance(dataset_info, dict):
                splits = dataset_info.get('splits', [])
                total_examples = 0
                for split in splits:
                    if isinstance(split, dict):
                        total_examples += split.get('num_examples', 0)
                return total_examples
            elif isinstance(dataset_info, list) and dataset_info:
                total_examples = 0
                for info in dataset_info:
                    splits = info.get('splits', [])
                    for split in splits:
                        if isinstance(split, dict):
                            total_examples += split.get('num_examples', 0)
                return total_examples
        return 0
    
    def get_description(self, parsed_data: Dict[str, Any]) -> str:
        return parsed_data.get('description', '')
    
    def get_metadata_completeness(self, parsed_data: Dict[str, Any]) -> float:
        card_data = parsed_data.get('cardData', {})
        
        metadata_fields = [
            'task_categories', 'language', 'size_categories', 
            'source_datasets', 'annotations_creators', 'language_creators'
        ]
        
        present_fields = 0
        for field in metadata_fields:
            if field in card_data and card_data[field]:
                value = card_data[field]
                if isinstance(value, list) and len(value) > 0:
                    present_fields += 1
                elif isinstance(value, str) and value.strip():
                    present_fields += 1
        
        return present_fields / len(metadata_fields)
    
    def has_citation(self, parsed_data: Dict[str, Any]) -> bool:
        citation = parsed_data.get('citation', '')
        return bool(citation and len(citation.strip()) > 20)
    
    def get_data_format_info(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        card_data = parsed_data.get('cardData', {})
        dataset_info = card_data.get('dataset_info', {})
        
        format_info = {
            'has_features': False,
            'feature_count': 0,
            'has_splits': False,
            'split_count': 0
        }
        
        if isinstance(dataset_info, dict):
            features = dataset_info.get('features', [])
            splits = dataset_info.get('splits', [])
            
            format_info['has_features'] = len(features) > 0
            format_info['feature_count'] = len(features)
            format_info['has_splits'] = len(splits) > 0
            format_info['split_count'] = len(splits)
        
        return format_info
    
    def get_data(self, parsed_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not parsed_data or parsed_data.get('category') != 'DATASET':
            return None

        card_data = parsed_data.get('cardData', {})
        dataset_info = card_data.get('dataset_info', {})
        metadata = parsed_data.get('metadata', {})

        # --- Make sure example_count is calculated ---
        example_count = 0
        splits = dataset_info.get('splits', [])
        if isinstance(splits, list):
            for split in splits:
                if isinstance(split, dict):
                    example_count += split.get('num_examples', 0)

        features = dataset_info.get('features', [])
        has_features = len(features) > 0
        has_splits = len(splits) > 0

        format_info = {
            'has_features': has_features,
            'has_splits': has_splits,
            'feature_count': len(features),
            'split_count': len(splits)
        }

        description = parsed_data.get('description', '') or metadata.get('description', '')
        citation = parsed_data.get('citation', '') or metadata.get('citation', '')
        downloads = parsed_data.get('downloads', 0) or metadata.get('downloads', 0)
        likes = parsed_data.get('likes', 0) or metadata.get('likes', 0)
        tags = parsed_data.get('tags', []) or metadata.get('tags', [])

        result = {
            'category': parsed_data.get('category', ''),
            'description': description,
            'example_count': example_count,  # ✅ <- This was missing before
            'metadata_completeness': self.get_metadata_completeness(parsed_data),
            'has_citation': bool(citation and len(citation.strip()) > 20),
            'format_info': format_info,
            'card_data': card_data,
            'downloads': downloads,
            'likes': likes,
            'tags': tags
        }

        return result

    # def get_data(self, parsed_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    #     if not parsed_data or parsed_data.get('category') != 'DATASET':
    #         return None
        
    #     card_data = parsed_data.get('cardData', {})
    #     dataset_info = card_data.get('dataset_info', {})
    #     metadata = parsed_data.get('metadata', {})
        
    #     example_count = 0
    #     splits = dataset_info.get('splits', [])
    #     for split in splits:
    #         if isinstance(split, dict):
    #             example_count += split.get('num_examples', 0)
        
    #     features = dataset_info.get('features', [])
    #     has_features = len(features) > 0
    #     has_splits = len(splits) > 0
        
    #     format_info = {
    #         'has_features': has_features,
    #         'has_splits': has_splits,
    #         'feature_count': len(features),
    #         'split_count': len(splits)
    #     }
        
    #     description = parsed_data.get('description', '') or metadata.get('description', '')
    #     citation = parsed_data.get('citation', '') or metadata.get('citation', '')
    #     downloads = parsed_data.get('downloads', 0) or metadata.get('downloads', 0)
    #     likes = parsed_data.get('likes', 0) or metadata.get('likes', 0)
    #     tags = parsed_data.get('tags', []) or metadata.get('tags', [])
        
    #     result = {
    #         'category': parsed_data.get('category', ''),
    #         'description': description,
    #         'example_count': example_count,
    #         'metadata_completeness': self.get_metadata_completeness(parsed_data),
    #         'has_citation': bool(citation and len(citation.strip()) > 20),
    #         'format_info': format_info,
    #         'card_data': card_data,
    #         'downloads': downloads,
    #         'likes': likes,
    #         'tags': tags
    #     }
        
    #     return result

    def calculate_score(self, data: Optional[Dict[str, Any]]) -> None:
        """
            Giving weight to each category. The more information available will have a better weight. 
        """
        if not data:
            self.dataset_quality = 0.0
            return
        
        score = 0.0


        example_count = data.get('example_count', 0)

        if example_count > 10000000:
            score += 0.35
        elif example_count > 1000000:
            score += 0.30
        elif example_count > 100000:
            score += 0.20
        elif example_count > 10000:
            score += 0.12
        elif example_count > 1000:
            score += 0.08
        elif example_count > 0:
            score += 0.05
        
        description = data.get('description', "")
        if len(description) > 500:
            score += 0.25
        elif len(description) > 300:
            score += 0.20
        elif len(description) > 150:
            score += 0.15
        elif len(description) > 75:
            score += 0.10
        elif len(description) > 25:
            score += 0.05
        
        metadata_score = data.get('metadata_completeness', 0) * 0.20
        score += metadata_score
        
        format_info = data.get('format_info', {})
        if format_info.get('has_features') and format_info.get('has_splits'):
            score += 0.10
        elif format_info.get('has_features') or format_info.get('has_splits'):
            score += 0.05


        
        if data.get('has_citation', False):
            score += 0.05
        
        downloads = data.get('downloads', 0)
        likes = data.get('likes', 0)
        
        if downloads > 5000 or likes > 50:
            score += 0.05
        elif downloads > 1000 or likes > 10:
            score += 0.03
        elif downloads > 100 or likes > 5:
            score += 0.02
        
        self.dataset_quality = min(1.0, score)
    
    def process_score(self, parsed_data: Dict[str, Any]) -> None:
        start_time = time.perf_counter()
        data = self.get_data(parsed_data)
        self.calculate_score(data)
        end_time = time.perf_counter()
        self.dataset_quality_latency = (end_time - start_time) * 1000.0