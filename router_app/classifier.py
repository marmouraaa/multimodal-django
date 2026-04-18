# router_app/classifier.py
import os
import json
import filetype
import magic

class ModalityClassifier:
    def __init__(self):
        self.mime_to_modality = {
            # Documents
            "application/pdf": "document",
            "application/msword": "document",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "document",
            "application/vnd.ms-powerpoint": "document",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation": "document",
            "text/plain": "document",
            "text/html": "document",
            "text/rtf": "document",
            
            # Images
            "image/jpeg": "image",
            "image/png": "image",
            "image/gif": "image",
            "image/webp": "image",
            "image/bmp": "image",
            "image/tiff": "image",
            "image/svg+xml": "image",
            
            # Vidéos
            "video/mp4": "video",
            "video/mpeg": "video",
            "video/quicktime": "video",
            
            # Données structurées
            "text/csv": "structured",
            "application/json": "structured",
            "application/xml": "structured",
            "text/xml": "structured",
            "application/vnd.ms-excel": "structured",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "structured",
        }
    
    def _is_json(self, content):
        try:
            content = content.strip()
            if content and (content[0] == '{' or content[0] == '['):
                json.loads(content)
                return True
            return False
        except:
            return False
    
    def _is_csv(self, content):
        try:
            lines = content.strip().split('\n')
            if len(lines) < 2:
                return False
            first_line = lines[0]
            if ',' not in first_line and ';' not in first_line:
                return False
            separator = ',' if ',' in first_line else ';'
            num_fields = len(first_line.split(separator))
            for line in lines[1:min(4, len(lines))]:
                if len(line.split(separator)) != num_fields:
                    return False
            return True
        except:
            return False
    
    def _read_text_content(self, file_path, max_size=10000):
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    return f.read(max_size)
            except:
                continue
        try:
            with open(file_path, 'rb') as f:
                return f.read(max_size).decode('latin-1', errors='ignore')
        except:
            return ""
    
    def classify(self, file_path):
        class Result:
            pass
        result = Result()
        
        if not os.path.exists(file_path):
            result.modality = "unknown"
            result.confidence = 0.0
            result.mime = None
            result.method = "file_not_found"
            return result
        
        # PRIORITÉ 1 : Analyse de contenu (JSON/CSV)
        content = self._read_text_content(file_path)
        if content:
            if self._is_json(content):
                result.modality = "structured"
                result.confidence = 0.95
                result.mime = "application/json"
                result.method = "json_content"
                return result
            
            if self._is_csv(content):
                result.modality = "structured"
                result.confidence = 0.95
                result.mime = "text/csv"
                result.method = "csv_content"
                return result
        
        # PRIORITÉ 2 : filetype
        try:
            ft = filetype.guess(file_path)
            if ft and ft.mime in self.mime_to_modality:
                result.modality = self.mime_to_modality[ft.mime]
                result.confidence = 0.98
                result.mime = ft.mime
                result.method = "filetype"
                return result
        except:
            pass
        
        # PRIORITÉ 3 : python-magic
        try:
            mime = magic.from_file(file_path, mime=True)
            if mime and mime in self.mime_to_modality:
                result.modality = self.mime_to_modality[mime]
                result.confidence = 0.95
                result.mime = mime
                result.method = "python-magic"
                return result
        except:
            pass
        
        # INCONNU
        result.modality = "unknown"
        result.confidence = 0.40
        result.mime = None
        result.method = "unknown"
        return result