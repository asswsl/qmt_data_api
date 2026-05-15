param(
    [string]$HostName = "127.0.0.1",
    [int]$Port = 8000
)

uvicorn qmt_data_api.main:app --host $HostName --port $Port --reload
