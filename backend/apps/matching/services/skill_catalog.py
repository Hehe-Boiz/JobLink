from decimal import Decimal


SKILL_ALIASES: dict[str, tuple[str, ...]] = {
    # canonical name
    "python": (
        "python", # alias
    ),
    "java": (
        "java",
    ),
    "javascript": (
        "javascript",
        "java script",
    ),
    "typescript": (
        "typescript",
        "type script",
    ),
    "c": (
        "c",
    ),
    "c++": (
        "c++",
        "cpp",
    ),
    "c#": (
        "c#",
        "c sharp",
    ),
    ".net": (
        ".net",
        "dotnet",
        "asp.net",
    ),
    "django": (
        "django",
    ),
    "django rest framework": (
        "django rest framework",
        "drf",
    ),
    "flask": (
        "flask",
    ),
    "fastapi": (
        "fastapi",
        "fast api",
    ),
    "spring": (
        "spring",
        "spring framework",
    ),
    "spring boot": (
        "spring boot",
        "springboot",
    ),
    "react": (
        "react",
        "react.js",
        "reactjs",
    ),
    "react native": (
        "react native",
        "react-native",
    ),
    "node.js": (
        "node.js",
        "nodejs",
        "node js",
    ),
    "postgresql": (
        "postgresql",
        "postgres",
        "postgre sql",
    ),
    "mysql": (
        "mysql",
        "my sql",
    ),
    "mongodb": (
        "mongodb",
        "mongo db",
    ),
    "redis": (
        "redis",
    ),
    "docker": (
        "docker",
    ),
    "kubernetes": (
        "kubernetes",
        "k8s",
    ),
    "aws": (
        "aws",
        "amazon web services",
    ),
    "gcp": (
        "gcp",
        "google cloud platform",
    ),
    "azure": (
        "azure",
        "microsoft azure",
    ),
    "git": (
        "git",
    ),
    "linux": (
        "linux",
        "ubuntu",
    ),
    "rest api": (
        "rest api",
        "restful api",
        "restful web service",
        "restful web services",
    ),
    "pytorch": (
        "pytorch",
        "torch",
    ),
    "tensorflow": (
        "tensorflow",
        "tensor flow",
    ),
    "machine learning": (
        "machine learning",
    ),
    "deep learning": (
        "deep learning",
    ),
    "computer vision": (
        "computer vision",
    ),
    "natural language processing": (
        "natural language processing",
        "nlp",
    ),
    "rag": (
        "retrieval augmented generation",
        "rag",
    ),
}

RELATED_SKILLS = {
    "spring boot": {
        "spring": Decimal("0.50"),
    },
    "spring": {
        "spring boot": Decimal("0.90"),
    },
    "django rest framework": {
        "django": Decimal("0.60"),
    },
    "react native": {
        "react": Decimal("0.45"),
    },
    "postgresql": {
        "sql": Decimal("0.35"),
    },
    "kubernetes": {
        "docker": Decimal("0.30"),
    },
}