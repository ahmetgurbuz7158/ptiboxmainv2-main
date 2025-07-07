# Flask Web App Starter

## Cloud Run Deploy Talimatları

1. Google Cloud hesabınızda bir proje oluşturun.
2. Cloud Shell veya kendi makinenizde terminal açın.
3. Gerekirse Google Cloud SDK kurun ve giriş yapın:
   ```sh
   gcloud auth login
   gcloud config set project [PROJE_ID]
   ```
4. Cloud Run ve Container Registry API'lerini etkinleştirin:
   ```sh
   gcloud services enable run.googleapis.com containerregistry.googleapis.com
   ```
5. Docker image'ı build edin ve push edin:
   ```sh
   docker build -t gcr.io/[PROJE_ID]/ptiboxmain:latest .
   docker push gcr.io/[PROJE_ID]/ptiboxmain:latest
   ```
6. Cloud Run'a deploy edin:
   ```sh
   gcloud run deploy ptiboxmain \
     --image gcr.io/[PROJE_ID]/ptiboxmain:latest \
     --platform managed \
     --region europe-west1 \
     --allow-unauthenticated
   ```
7. Size verilen URL'i not alın. Bu URL'i Flutter WebView'da kullanacaksınız.

