# File Transfer

## Configuración inicial
Para poder correr la aplicación es necesario ejecutar los siguientes comandos:

```
chmod +x start-server
chmod +x upload
chmod +x download

python3 start-server -v
python3 upload -s test.txt -n test_file_txt
python3 download  -n test_file_txt
```

Para los distintos protocolos (defaultea a Stop & Wait):

```
-t sw
-t sr
```