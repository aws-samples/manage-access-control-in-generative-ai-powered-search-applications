init:
	python3 -m venv venv
	source venv/bin/activate
	@cd cdk-infrastructure && pip install -r requirements.txt && pip install -r requirements-dev.txt

bootstrap-cdk:
	@cd cdk-infrastructure && npx cdk bootstrap

deploy-cdk:
	@cd cdk-infrastructure && cdk deploy

deploy-cdk-with-mock-users:
	@cd cdk-infrastructure && cdk deploy && ./create_test_users.sh

mock-users:
	@cd cdk-infrastructure && ./create_test_users.sh

destroy:
	@cd cdk-infrastructure && ./destroy.sh

install-frontend:
	@cd frontend && npm ci

run-frontend:
	@cd frontend && ./get_envs.sh && npm run dev

install-run-frontend: install-frontend run-frontend

style:
	@cd cdk-infrastructure && isort simple_rag_with_access_control/. && black .