from wasmtime import Store, Module, Instance
from importlib.resources import files

# Assuming 'nepse.wasm' is in the same package as this script
WASM_FILE = str(files(__package__) / 'nepse.wasm')
ROOT_URL = 'https://www.nepalstock.com'



class TokenParser():
    def __init__(self):
        self.store = Store()
        module = Module.from_file(self.store.engine, WASM_FILE)
        instance = Instance(self.store, module, [])

        self.cdx = instance.exports(self.store)["cdx"]
        self.rdx = instance.exports(self.store)["rdx"]
        self.bdx = instance.exports(self.store)["bdx"]
        self.ndx = instance.exports(self.store)["ndx"]
        self.mdx = instance.exports(self.store)["mdx"]

    def parse_token_response(self, token_response):
        n = self.cdx(self.store, token_response['salt1'], token_response['salt2'],
                     token_response['salt3'], token_response['salt4'], token_response['salt5'])
        l = self.rdx(self.store, token_response['salt1'], token_response['salt2'],
                     token_response['salt4'], token_response['salt3'], token_response['salt5'])
        o = self.bdx(self.store, token_response['salt1'], token_response['salt2'],
                     token_response['salt4'], token_response['salt3'], token_response['salt5'])
        p = self.ndx(self.store, token_response['salt1'], token_response['salt2'],
                     token_response['salt4'], token_response['salt3'], token_response['salt5'])
        q = self.mdx(self.store, token_response['salt1'], token_response['salt2'],
                     token_response['salt4'], token_response['salt3'], token_response['salt5'])
        i = self.cdx(self.store, token_response['salt2'], token_response['salt1'],
                     token_response['salt3'], token_response['salt5'], token_response['salt4'])
        r = self.rdx(self.store, token_response['salt2'], token_response['salt1'],
                     token_response['salt3'], token_response['salt4'], token_response['salt5'])
        s = self.bdx(self.store, token_response['salt2'], token_response['salt1'],
                     token_response['salt4'], token_response['salt3'], token_response['salt5'])
        t = self.ndx(self.store, token_response['salt2'], token_response['salt1'],
                     token_response['salt4'], token_response['salt3'], token_response['salt5'])
        u = self.mdx(self.store, token_response['salt2'], token_response['salt1'],
                     token_response['salt4'], token_response['salt3'], token_response['salt5'])

        access_token = token_response['accessToken']
        refresh_token = token_response['refreshToken']

        parsed_access_token = access_token[0:n] + access_token[n+1:l] + access_token[l +
                                                                                     1:o] + access_token[o+1:p] + access_token[p+1:q] + access_token[q+1:]
        parsed_refresh_token = refresh_token[0:i] + refresh_token[i+1:r] + refresh_token[r +
                                                                                         1:s] + refresh_token[s+1:t] + refresh_token[t+1:u] + refresh_token[u+1:]

        return (parsed_access_token, parsed_refresh_token)
