package diptestbed.domain

import java.nio.charset.{Charset, StandardCharsets}
import io.github.nremond.PBKDF2
import diptestbed.domain.Charsets.{ByteOps, StringOps, defaultCharset}
import diptestbed.domain.Salt.saltCharset
import java.util.Base64
import scala.util.Try

object Charsets {
  val defaultCharset: Charset = StandardCharsets.UTF_8
  implicit class StringOps(value: String) {
    def toBase64(charset: Charset = defaultCharset): String =
      Base64.getEncoder.encodeToString(value.asCharsetBytes(charset))

    def fromBase64(charset: Charset = defaultCharset): Option[String] =
      Try(Base64.getDecoder.decode(value).asCharsetString(charset)).toOption

    def asCharsetBytes(charset: Charset = defaultCharset): Array[Byte] =
      value.getBytes(charset)
  }

  implicit class ByteOps(value: Array[Byte]) {
    def asCharsetString(charset: Charset = defaultCharset): String =
      new String(value, charset)
  }
}

case class HashedPassword(salt: Salt, hash: Hash) {
  def toSerializedString: String = {
    s"${salt.value}:${hash.value}"
  }
}
object HashedPassword {
  def fromSerializedString(value: String): Option[HashedPassword] =
    value.split(":").toList match {
      case salt :: hash :: Nil => Some(HashedPassword(Salt(salt), Hash(hash)))
      case _                   => None
    }

  def fromBytePassword(
    password: Array[Byte],
    salt: Salt = Salt.randomSalt(),
    iterations: Int = 20000,
    keyLength: Int = 32,
  ): HashedPassword =
    HashedPassword(
      salt,
      Hash.fromBytes(
        PBKDF2(
          password,
          salt.toBytes(),
          iterations,
          keyLength,
        ),
      ),
    )

  def fromPassword(
    password: String,
    salt: Salt = Salt.randomSalt(),
    iterations: Int = 20000,
    keyLength: Int = 32,
  ): HashedPassword =
    HashedPassword.fromBytePassword(
      password.asCharsetBytes(defaultCharset),
      salt,
      iterations,
      keyLength,
    )
}

case class Salt(value: String) {
  def toBytes() = value.asCharsetBytes(saltCharset)
}
object Salt {
  private val saltCharset = defaultCharset
  def randomSalt(bytes: Int = 64): Salt =
    Salt(Bytes.random(bytes).asCharsetString(defaultCharset).toBase64())
}

case class Hash(value: String)
object Hash {
  private val hashCharset = defaultCharset
  def fromBytes(bytes: Array[Byte]) = Hash(bytes.asCharsetString(hashCharset).toBase64())
}

object Bytes {
  def random(bytes: Int): Array[Byte] =
    Array.fill(bytes)((scala.util.Random.nextInt(256) - 128).toByte)
}
