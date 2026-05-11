# Тести для Flask API — Генетичний алгоритм складання розкладу
import pytest
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api import app, ScheduleData, ScheduleOptimizer


# ── Flask test client ────────────────────────────────────────
@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c


# ── /health ──────────────────────────────────────────────────
def test_health_endpoint(client):
    """GET /health повертає статус ok"""
    response = client.get('/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'ok'


# ── /calculate — базовий запит ───────────────────────────────
def test_calculate_empty_body(client):
    """POST /calculate з порожнім тілом повертає 200"""
    response = client.post('/calculate',
                           data=json.dumps({}),
                           content_type='application/json')
    assert response.status_code == 200


def test_calculate_returns_success(client):
    """Відповідь містить status: success"""
    response = client.post('/calculate',
                           data=json.dumps({}),
                           content_type='application/json')
    data = json.loads(response.data)
    assert data['status'] == 'success'


def test_calculate_has_result_fields(client):
    """Відповідь містить всі обов'язкові поля result"""
    response = client.post('/calculate',
                           data=json.dumps({
                               'max_iterations': 5,
                               'population_size': 10
                           }),
                           content_type='application/json')
    data = json.loads(response.data)
    result = data['result']
    for field in ('conflicts', 'gaps', 'preference_deviation',
                  'final_score', 'iterations_done', 'schedule_size',
                  'schedule_preview'):
        assert field in result, f"Поле '{field}' відсутнє у result"


def test_calculate_custom_params(client):
    """Передані параметри відображаються у полі input"""
    payload = {'num_lecturers': 5, 'num_subjects': 10,
               'max_iterations': 5, 'population_size': 10}
    response = client.post('/calculate',
                           data=json.dumps(payload),
                           content_type='application/json')
    data = json.loads(response.data)
    assert data['input']['num_lecturers'] == 5
    assert data['input']['num_subjects'] == 10


def test_calculate_conflicts_non_negative(client):
    """Кількість конфліктів не може бути від'ємною"""
    response = client.post('/calculate',
                           data=json.dumps({
                               'max_iterations': 5,
                               'population_size': 10
                           }),
                           content_type='application/json')
    data = json.loads(response.data)
    assert data['result']['conflicts'] >= 0


def test_calculate_schedule_preview_length(client):
    """schedule_preview містить не більше 5 елементів"""
    response = client.post('/calculate',
                           data=json.dumps({
                               'max_iterations': 5,
                               'population_size': 10
                           }),
                           content_type='application/json')
    data = json.loads(response.data)
    assert len(data['result']['schedule_preview']) <= 5


# ── ScheduleData unit tests ───────────────────────────────────
def test_schedule_data_creation():
    """ScheduleData створює правильну кількість об'єктів"""
    data = ScheduleData(num_lecturers=5, num_subjects=10,
                        num_rooms=4, num_groups=3)
    assert len(data.lecturers) == 5
    assert len(data.subjects) == 10
    assert len(data.rooms) == 4
    assert len(data.groups) == 3


def test_schedule_data_total_slots():
    """total_slots = days * slots_per_day"""
    data = ScheduleData()
    assert data.total_slots == data.days * data.slots_per_day


# ── ScheduleOptimizer unit tests ─────────────────────────────
def test_optimizer_creates_schedule():
    """Оптимізатор повертає розклад правильного розміру"""
    data = ScheduleData(num_lecturers=3, num_subjects=5,
                        num_rooms=3, num_groups=2)
    opt = ScheduleOptimizer(data, population_size=5, max_iterations=3)
    schedule = opt.optimize()
    assert len(schedule) == 5


def test_optimizer_conflicts_non_negative():
    """check_conflicts повертає невід'ємне число"""
    data = ScheduleData(num_lecturers=3, num_subjects=5,
                        num_rooms=3, num_groups=2)
    opt = ScheduleOptimizer(data, population_size=5, max_iterations=3)
    schedule = opt.create_random_schedule()
    assert opt.check_conflicts(schedule) >= 0


def test_optimizer_objective_non_negative():
    """objective_function повертає невід'ємне число"""
    data = ScheduleData(num_lecturers=3, num_subjects=5,
                        num_rooms=3, num_groups=2)
    opt = ScheduleOptimizer(data, population_size=5, max_iterations=3)
    schedule = opt.create_random_schedule()
    assert opt.objective_function(schedule) >= 0
