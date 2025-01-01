import os
import boto3

class ParameterStore:
    SSM_PARAMETERS = {
        'OPENAI_API_KEY': '/DEV/CICD/MUSEIFY/OPENAI_API_KEY',
        'UPSTAGE_API_KEY': '/DEV/CICD/MUSEIFY/UPSTAGE_API_KEY',
        'COHERE_API_KEY': '/DEV/CICD/MUSEIFY/COHERE_API_KEY',
        'MONGO_URI': '/DEV/CICD/MUSEIFY/MONGO_URI',
        'MONGO_DB_NAME': '/DEV/CICD/MUSEIFY/MONGO_DB_NAME',
        'MONGO_VECTOR_DB_NAME': '/DEV/CICD/MUSEIFY/MONGO_VECTOR_DB_NAME',
        'KOPIS_API_KEY': '/DEV/CICD/MUSEIFY/KOPIS_API_KEY'
    }

    @staticmethod
    def init_services():
        os.environ['OPENAI_API_KEY'] = ParameterStore.get_parameter('OPENAI_API_KEY')
        os.environ['UPSTAGE_API_KEY'] = ParameterStore.get_parameter('UPSTAGE_API_KEY')
        os.environ['COHERE_API_KEY'] = ParameterStore.get_parameter('COHERE_API_KEY')
        os.environ['MONGO_URI'] = ParameterStore.get_parameter('MONGO_URI')
        os.environ['MONGO_DB_NAME'] = ParameterStore.get_parameter('MONGO_DB_NAME')
        os.environ['MONGO_VECTOR_DB_NAME'] = ParameterStore.get_parameter('MONGO_VECTOR_DB_NAME')
        os.environ['KOPIS_API_KEY'] = ParameterStore.get_parameter('KOPIS_API_KEY')

    @staticmethod
    def get_parameter(param_name):
        value = os.environ.get(param_name)
        
        if not value and param_name in ParameterStore.SSM_PARAMETERS:
            try:
                ssm = boto3.client('ssm')
                parameter = ssm.get_parameter(
                    Name=ParameterStore.SSM_PARAMETERS[param_name],
                    WithDecryption=True
                )
                value = parameter['Parameter']['Value']
                os.environ[param_name] = value 
            except Exception as e:
                raise ValueError(f"{param_name} 파라미터 조회 중 오류 발생: {str(e)}")
        
        if not value:
            raise ValueError(f"{param_name}가 설정되지 않았습니다.")
        
        return value

    @staticmethod
    def set_all_parameters():
        parameters = {}
        for param_name in ParameterStore.SSM_PARAMETERS.keys():
            parameters[param_name] = ParameterStore.get_parameter(param_name)
        return parameters