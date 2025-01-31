import multibase

from typing import Optional

from nacl.bindings.crypto_secretstream import (
    crypto_secretstream_xchacha20poly1305_ABYTES,
    crypto_secretstream_xchacha20poly1305_TAG_FINAL,
    crypto_secretstream_xchacha20poly1305_TAG_MESSAGE,
    crypto_secretstream_xchacha20poly1305_init_pull,
    crypto_secretstream_xchacha20poly1305_init_push,
    crypto_secretstream_xchacha20poly1305_pull,
    crypto_secretstream_xchacha20poly1305_push,
    crypto_secretstream_xchacha20poly1305_state,
)

from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
from cryptography.hazmat.primitives import serialization

from millegrilles_messages.messages.EnveloppeCertificat import EnveloppeCertificat
from millegrilles_messages.messages.Hachage import hacher_to_digest
from millegrilles_messages.chiffrage.ChiffrageUtils import generer_info_chiffrage
from millegrilles_messages.messages.Hachage import Hacheur

CONST_TAILLE_BUFFER = 64 * 1024
CONST_TAILLE_DATA = CONST_TAILLE_BUFFER - crypto_secretstream_xchacha20poly1305_ABYTES


class CipherMgs4:

    def __init__(self, public_key: X25519PublicKey):
        self.__cle_secrete: Optional[bytes] = None
        self.__tag: Optional[bytes] = None
        self.__public_peer_x25519: Optional[X25519PublicKey] = None
        self.__hachage: Optional[str] = None

        self.__cle_secrete, self.__state, self.__header = self.__generer_cipher(public_key)

        self.__hacheur = Hacheur('blake2b-512', 'base58btc')

        self.__buffer = bytes()

    def __generer_cipher(self, public_key: X25519PublicKey):
        """
        Generer la cle secrete a partir d'une cle publique
        """
        # Generer cle peer
        key_x25519 = X25519PrivateKey.generate()
        self.__public_peer_x25519 = key_x25519.public_key()

        # Extraire la cle secrete avec exchange
        cle_handshake = key_x25519.exchange(public_key)

        # Hacher avec blake2s-256
        cle_secrete = hacher_to_digest(cle_handshake, 'blake2s-256')

        state = crypto_secretstream_xchacha20poly1305_state()

        # Creer cipher (inclus nonce)
        header = crypto_secretstream_xchacha20poly1305_init_push(state, cle_secrete)

        return cle_secrete, state, header

    @property
    def header(self) -> bytes:
        return self.__header

    def update(self, data: bytes) -> Optional[bytes]:
        data_out = bytes()

        while len(data) > 0:
            taille_max = CONST_TAILLE_DATA - len(self.__buffer)
            taille_chunk = min(taille_max, len(data))

            self.__buffer = self.__buffer + data[:taille_chunk]
            data = data[taille_chunk:]

            if len(self.__buffer) == CONST_TAILLE_DATA:
                data_chiffre = crypto_secretstream_xchacha20poly1305_push(self.__state, self.__buffer)
                self.__hacheur.update(data_chiffre)
                data_out = data_out + data_chiffre

                self.__buffer = bytes()  # Clear buffer

        return data_out

    def finalize(self) -> bytes:
        if self.__hachage is not None:
            raise Exception('Already finalized')

        data_out = crypto_secretstream_xchacha20poly1305_push(
            self.__state, self.__buffer, tag=crypto_secretstream_xchacha20poly1305_TAG_FINAL)

        self.__hachage = self.__hacheur.finalize()

        return data_out

    def get_info_dechiffrage(self, enveloppes: Optional[list[EnveloppeCertificat]] = None) -> dict:
        key_x25519_public_bytes = self.__public_peer_x25519.public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw)
        return generer_info_chiffrage(self.__cle_secrete, None, None, self.__header, self.__hachage,
                                      enveloppes, public_peer=key_x25519_public_bytes)


class DecipherMgs4:

    def __init__(self, cle_secrete: bytes, header: bytes):

        if header is not None:
            if isinstance(header, str):
                header = multibase.decode(header)
            elif isinstance(header, bytes):
                pass  # Ok
            else:
                raise TypeError('type tag non supporte (valides: str, bytes)')

        self.__state = crypto_secretstream_xchacha20poly1305_state()
        crypto_secretstream_xchacha20poly1305_init_pull(self.__state, header, cle_secrete)

        self.__buffer = bytes()

    @staticmethod
    def from_info(clecert, info_dechiffrage: dict):
        header = info_dechiffrage['header']

        # Dechiffrer cle
        cle_chiffree = info_dechiffrage['cles'][clecert.enveloppe.fingerprint]
        cle_secrete = clecert.dechiffrage_asymmetrique(cle_chiffree)

        return DecipherMgs4(cle_secrete, header)

    def update(self, data: bytes) -> bytes:
        data_out = bytes()

        while len(data) > 0:
            taille_max = CONST_TAILLE_BUFFER - len(self.__buffer)
            taille_chunk = min(taille_max, len(data))

            self.__buffer = self.__buffer + data[:taille_chunk]
            data = data[taille_chunk:]

            if len(self.__buffer) == CONST_TAILLE_BUFFER:
                data_dechiffre, tag = crypto_secretstream_xchacha20poly1305_pull(self.__state, self.__buffer)
                if tag != crypto_secretstream_xchacha20poly1305_TAG_MESSAGE:
                    raise Exception("Erreur dechiffrage fichier (tag != TAG_MESSAGE)")
                data_out = data_out + data_dechiffre
                self.__buffer = bytes()  # Clear buffer

        return data_out

    def finalize(self) -> bytes:
        data_out, tag = crypto_secretstream_xchacha20poly1305_pull(self.__state, self.__buffer)
        if tag != crypto_secretstream_xchacha20poly1305_TAG_FINAL:
            raise Exception("Erreur dechiffrage final (mauvais tag)")

        return data_out
