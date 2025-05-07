import zipfile
import os

def zipdir(path, ziph):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            file_path = os.path.join(root, file)
            ziph.write(file_path, 
                      os.path.relpath(file_path, 
                                     os.path.join(path, '..')))

with zipfile.ZipFile('ProgressGhostCreator.zip', 'w', zipfile.ZIP_DEFLATED) as zipf:
    zipdir('download_package/', zipf)
    
print("Zip file created: ProgressGhostCreator.zip")
