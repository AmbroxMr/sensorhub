# SensorHub — despliegue K8s (sin Helm)

Manifiestos "a pelo" para desplegar la aplicación. Las dependencias
(MongoDB, MinIO, RabbitMQ) se instalan previamente con Helm.

## Requisitos

- `kubectl` configurado contra el cluster
- `helm` instalado
- Imágenes construidas y disponibles en el cluster:
  ```
  docker build -t sensorhub:latest .
  docker build -t sensorhub-frontend:latest -f Dockerfile.frontend .
  ```
  > Con Minikube: `eval $(minikube docker-env)` antes de construir.

---

## 1. Namespace

```bash
kubectl apply -f namespace.yaml
```

---

## 2. Dependencias con Helm

```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
```

### MongoDB

```bash
helm install mongodb bitnami/mongodb -n sensorhub \
  --set auth.rootPassword=changeme \
  --set auth.username=root \
  --set auth.database=sensorhub \
  --set persistence.size=1Gi \
  --set persistence.storageClass=standard
```

### MinIO

```bash
helm install minio bitnami/minio -n sensorhub \
  --set auth.rootUser=minioadmin \
  --set auth.rootPassword=changeme \
  --set provisioning.enabled=true \
  --set provisioning.buckets[0].name=bucket \
  --set persistence.size=2Gi \
  --set persistence.storageClass=standard
```

### RabbitMQ

```bash
helm install rabbitmq bitnami/rabbitmq -n sensorhub \
  --set auth.username=guest \
  --set auth.password=guest \
  --set persistence.size=1Gi \
  --set persistence.storageClass=standard
```

Espera a que los pods estén `Running` antes de continuar:

```bash
kubectl get pods -n sensorhub -w
```

---

## 3. ConfigMap y Secret

```bash
kubectl apply -f configmap.yaml
kubectl apply -f secret.yaml
```

> Edita `configmap.yaml` y `secret.yaml` si cambiaste usuarios/contraseñas en el paso anterior.

---

## 4. Aplicación

```bash
kubectl apply -f api-deployment.yaml
kubectl apply -f api-service.yaml
kubectl apply -f worker-deployment.yaml
kubectl apply -f frontend-deployment.yaml
kubectl apply -f frontend-service.yaml
```

O de una vez:

```bash
kubectl apply -f .
```

---

## 5. Verificación

```bash
# Estado de los pods
kubectl get pods -n sensorhub

# Logs de la API
kubectl logs -n sensorhub deploy/api

# Logs del worker
kubectl logs -n sensorhub deploy/worker
```

### Acceso (Minikube)

```bash
minikube service api      -n sensorhub --url   # API    → :30800
minikube service frontend -n sensorhub --url   # UI     → :30801
minikube service minio    -n sensorhub --url   # MinIO  → :30900 / :30901
minikube service rabbitmq -n sensorhub --url   # RabbitMQ management → :31672
```

---

## Puertos NodePort asignados

| Servicio          | Puerto interno | NodePort |
|-------------------|----------------|----------|
| API               | 8000           | 30800    |
| Frontend          | 8501           | 30801    |
| MinIO API         | 9000           | 30900    |
| MinIO Console     | 9001           | 30901    |
| RabbitMQ AMQP     | 5672           | 30672    |
| RabbitMQ Mgmt UI  | 15672          | 31672    |

---

## Desinstalar todo

```bash
kubectl delete namespace sensorhub
helm uninstall mongodb minio rabbitmq -n sensorhub
```
