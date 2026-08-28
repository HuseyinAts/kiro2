# CQRS Migration Guide (August 2026 Ultra Standard)

## Problemin Tanımı: API Bloat & "1,226 Endpoint" Sorunu
Şu an `backend/api/` altında 1,226 adet farklı endpoint bulunmaktadır. Single Responsibility Principle (SRP) çiğnenmiş ve business katmanı (servisler, DB çağrıları) doğrudan router'ların (FastAPI endpoints) içine sızmıştır.
Bu durum, sistemin test edilebilirliğini düşürmekte, kod okumasını zorlaştırmakta ve performans darboğazları (deadlock vs.) yaratmaktadır.

## Çözüm: CQRS (Command Query Responsibility Segregation)
"Ultra" standartlarına ulaşmak için tüm API'nin CQRS mimarisine taşınması için altyapı oluşturulmuştur.
Altyapı, `backend/core/cqrs/` altında hazır bulunmaktadır:
- `Command` ve `CommandHandler` (Yazma/Değiştirme işlemleri için)
- `Query` ve `QueryHandler` (Sadece Okuma işlemleri için)
- `CommandBus` ve `QueryBus` (Bu handler'lara telemetri ve hata yönetimi ile istekleri iletmek için)

## Nasıl Uygulanır? (Örnek)

### 1. Command/Query Sınıfını Tanımlayın (Örn: `backend/application/commands/auth.py`)
```python
from core.cqrs import Command, CommandHandler

class CreateUserCommand(Command):
    email: str
    password: str

class CreateUserCommandHandler(CommandHandler[CreateUserCommand, dict]):
    async def handle(self, command: CreateUserCommand) -> dict:
        # DB işlemi ve business logic burada olacak
        return {"id": "123", "email": command.email}
```

### 2. Handler'ı Bus'a Kaydedin (Örn: `backend/main.py` veya `backend/application/bootstrap.py`)
```python
from core.cqrs import get_command_bus
from application.commands.auth import CreateUserCommand, CreateUserCommandHandler

command_bus = get_command_bus()
command_bus.register(CreateUserCommand, CreateUserCommandHandler())
```

### 3. API Route'unda Bus Kullanımı (Örn: `backend/api/auth.py`)
```python
from fastapi import APIRouter
from core.cqrs import get_command_bus
from application.commands.auth import CreateUserCommand

router = APIRouter()
command_bus = get_command_bus()

@router.post("/users")
async def create_user(command: CreateUserCommand):
    # Tüm business logic ve DB oturumu CommandHandler içinde izole edildi!
    result = await command_bus.execute(command)
    return result
```

## Yol Haritası
1. Yeni yazılacak her modül bu yapıya uymak ZORUNDADIR.
2. Mevcut `backend/api/` içindeki en şişkin endpointler (örn. `auth.py`, `learning_path_v2.py`) takım lideri eşliğinde parçalanarak `backend/application/queries/` ve `backend/application/commands/` altına taşınmalıdır.
3. FastAPI sadece HTTP request-response parsing ve routing'den sorumlu bırakılmalıdır.
