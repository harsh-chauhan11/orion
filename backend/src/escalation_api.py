import json

from escalation import get_escalations


def main():
    escalations = get_escalations()

    print(json.dumps(escalations))


if __name__ == "__main__":
    main()