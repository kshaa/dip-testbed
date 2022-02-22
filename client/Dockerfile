FROM ubuntu

# Install python through pyenv
ENV DEBIAN_FRONTEND="noninteractive"
RUN apt update && apt install -y lsb-release make build-essential libssl-dev zlib1g-dev \
    libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev\
    libncursesw5-dev xz-utils tk-dev libffi-dev liblzma-dev python-openssl\
    git

RUN git clone https://github.com/pyenv/pyenv.git /pyenv
ENV PYENV_ROOT="/pyenv"
ENV PYENV_SHELL="bash"
ENV PATH="${PYENV_ROOT}/bin:${PATH}"
ENV PYTHON_CONFIGURE_OPTS="--enable-shared"
RUN pyenv install -f 3.9.7
ENV PYENV_VERSION="3.9.7"
ENV PATH="/pyenv/shims:${PATH}"

# Install pipenv & pyinstaller
RUN pip install pipenv pyinstaller

# Copy app dependencies
COPY ./Pipfile /app/Pipfile
COPY ./Pipfile.lock /app/Pipfile.lock
WORKDIR /app/

# Install app dependencies
RUN pipenv install --system --deploy

# Copy app source code
COPY ./ /app/
WORKDIR /app/

# Run app build
RUN ./build.sh

# Remove stuff I don't need in the build
RUN apt-get purge -y lsb-release make build-essential libssl-dev zlib1g-dev \
    libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev \
    libncursesw5-dev xz-utils tk-dev libffi-dev liblzma-dev python-openssl \
    git && apt-get clean && rm -rf /pyenv /app/build
