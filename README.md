docker build -t flask-azure-docker .

docker run -p 5000:5000 -e AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=https;AccountName=uploadiamgestorage;AccountKey=EG/yNSo9mT+sUBOz62uyEc+8lJepAg3KnxeDo3fW/NVRhLQRcCsy3aUIPCs373gsND8+ZmIrc9+X+AStR42Low==;EndpointSuffix=core.windows.net" flask-azure-docker

python app.py

---

> docker start flask-azure-docker

## url 
for now 

http://localhost:5000/

