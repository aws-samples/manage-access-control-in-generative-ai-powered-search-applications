init:
	@cd cdk-infrastructure && pip install -r requirements.txt && pip install -r requirements-dev.txt

deploy-cdk:
	@cd cdk-infrastructure && cdk deploy

deploy-cdk-with-mock-users:
	@cd cdk-infrastructure && cdk deploy && ./create_test_users.sh

mock-users:
	@cd cdk-infrastructure && ./create_test_users.sh

install-amplify-frontend:
	@cd frontend && ./deploy.sh

install-run-local-frontend:
	@cd frontend && ./get_envs.sh && npm ci && npm run dev

destroy-backend:
	@cd cdk-infrastructure && ./cleanup.sh

destroy-frontend:
	@cd frontend && ./cleanup.sh

destroy: destroy-frontend destroy-backend

style:
	@cd cdk-infrastructure && isort simple_rag_with_access_control/. && black .