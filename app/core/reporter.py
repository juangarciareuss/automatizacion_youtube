"""
ARCHIVO: app/core/reporter.py

DESCRIPCIÓN Y FUNCIONALIDAD:
Este documento se encarga exclusivamente de documentar y registrar todo lo que 
ocurrió durante la creación de un video. No edita ni genera multimedia.

Su flujo exacto es:
1. Recibe el guion completo (script), el mapa con las rutas de los archivos visuales (assets_map) 
   y la ruta del video final ya renderizado (video_path).
2. Extrae la información general de la producción: título, formato, fecha y la "Biblia Visual" 
   (los parámetros de consistencia estética).
3. Itera sobre cada escena del guion para emparejar el texto narrado, el prompt visual utilizado 
   y la ubicación exacta del archivo multimedia generado para esa escena.
4. Escribe y guarda un archivo '.json' con todos estos datos estructurados (útil para auditoría técnica o bases de datos).
5. Escribe y guarda un archivo '.md' (Markdown) formateado para lectura humana, detallando paso a paso 
   qué hizo la IA en cada escena. Ambos archivos se guardan en la misma carpeta que el video final.
"""

import os
import time
import json
from app.utils.logger import get_logger

logger = get_logger("REPORTER")

class ReportGenerator:
    
    @staticmethod
    def save_production_report(script, assets_map, video_path):
        try:
            report_data = {
                "video_title": script.title,
                "timestamp": time.ctime(),
                "channel": script.orientation.name,
                "visual_bible": script.visual_bible.dict(),
                "scenes": []
            }

            for scene in script.scenes:
                report_data["scenes"].append({
                    "id": scene.id,
                    "narrative": scene.narrative_text,
                    "prompt_used": scene.action_prompt,
                    "asset_path": assets_map.get(scene.id, "MISSING")
                })

            # Guardar JSON
            json_path = video_path.replace(".mp4", "_data.json")
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(report_data, f, indent=4, ensure_ascii=False)

            # Guardar Markdown
            md_path = video_path.replace(".mp4", "_analisis.md")
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(f"# 🎬 Reporte de Producción: {script.title}\n\n")
                f.write(f"**Fecha:** {time.ctime()}\n")
                f.write(f"**Formato:** {script.orientation.name}\n")
                f.write(f"**Archivo:** `{os.path.basename(video_path)}`\n\n")
                
                f.write("## 🎨 Biblia Visual (Consistencia)\n")
                f.write(f"- **Hero Object:** {script.visual_bible.hero_object}\n")
                f.write(f"- **Surface:** {script.visual_bible.surface}\n")
                f.write(f"- **Lighting:** {script.visual_bible.lighting}\n\n")
                
                f.write("## Desglose de Escenas\n")
                for s in report_data["scenes"]:
                    f.write(f"### Escena {s['id']}\n")
                    f.write(f"- **Voz:** *{s['narrative']}*\n")
                    f.write(f"- **Visual:** {s['prompt_used']}\n")
                    f.write(f"- **Asset:** `{os.path.basename(s['asset_path'])}`\n\n")
                    
            logger.info(f"💾 Reportes guardados exitosamente junto al video.")
            
        except Exception as e:
            logger.error(f"❌ Falló la generación del reporte: {e}")