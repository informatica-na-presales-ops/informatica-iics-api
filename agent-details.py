import iics
import os


def main():
    client = iics.APIClient(os.getenv('IICS_POD_REGION', 'us'), os.getenv('IICS_USERNAME'), os.getenv('IICS_PASSWORD'))
    for agent in client.get_agent_details():
        agent_name = agent.get('name')
        for app in agent.get('agentEngines'):
            app_name = app.get('agentEngineStatus').get('appDisplayName')
            app_desired_status = app.get('agentEngineStatus').get('desiredStatus')
            app_status = app.get('agentEngineStatus').get('status')
            print(f'{agent_name} / {app_name} / desired: {app_desired_status} / current: {app_status}')


if __name__ == '__main__':
    main()
