To start the application:
  uvicorn main:app --host 0.0.0.0 --port 8000 --reload 


Команда сборки:
  apt-get update && apt-get install -y libgl1 && pip install -r requirements.txt && pip install python-dotenv && pip install uvicorn && pip install opencv-python 

<!-- 
  ngrok tunnel --label edge=edghts_2e99fhIZiOgao09G4cV0xGXmzEh http://localhost:8000 -->

Миграция алембик:
  alembic revision --autogenerate 

Накатить миграции:
  - alembic upgrade head
  -   alembic upgrade <revision>
  - alembic current — показать текущую ревизию.
  - alembic history — показать историю миграций.
  - alembic downgrade <revision> — откатить базу данных до указанной ревизии.
  - alembic revision --autogenerate -m "Сообщение" — создать новую миграцию на основе изменений схемы.
