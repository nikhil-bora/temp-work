
import json
from datetime import datetime

print('Hello from Python!')
print('Current time:', datetime.now().isoformat())

data = {
    'language': 'python',
    'timestamp': datetime.now().isoformat(),
    'test': 'successful'
}

print('Python test completed')
print(json.dumps(data, indent=2))
