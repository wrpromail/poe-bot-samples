def requirements_to_list(req_file="requirements.txt"):
    requirements = []
    with open(req_file, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                requirements.append(line)
    return requirements