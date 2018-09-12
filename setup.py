from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "tessa",
    version = "1.0.0",
    author = "Samu Juvonen",
    author_email = "samu.juvonen@gmail.com",
    description = "Simple btrfs snapshot utility with support for send/receive.",
    license = "BSD",
    keywords = "btrfs incremental snapshots ssh",
    url = "https://github.com/sjuvonen/tessa",
    packages = ["tessa"],
    scripts = ["bin/tessa"]
)
