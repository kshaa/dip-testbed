package iotfrisbee.domain

import cats.implicits.{catsStdInstancesForOption, catsSyntaxTuple2Semigroupal}

import java.nio.charset.StandardCharsets
//import com.roundeights.hasher.Algo
import io.github.nremond.PBKDF2
import java.util.Base64
import scala.util.Try

case class HashedPassword(salt: Salt, hash: Hash) {
  def toSerializedString: String =
    s"${salt.toBase64}:${hash.toBase64}"
}
object HashedPassword {
  def fromSerializedString(value: String): Option[HashedPassword] =
    value.split(":").toList match {
      case saltString :: hashString :: Nil =>
        val hashWithSalt = (Salt.fromBase64(saltString), Hash.fromBase64(hashString)).tupled
        hashWithSalt.map { case (hash, salt) => HashedPassword(hash, salt) }
      case _ => None
    }

  def fromPassword(
    password: String,
    salt: Salt = Salt.randomSalt(),
    iterations: Int = 20000,
    keyLength: Int = 32,
  ): HashedPassword = {
    val hash = Hash(
      PBKDF2(
        password.getBytes(StandardCharsets.UTF_8),
        salt.value,
        iterations,
        keyLength,
      ),
    )
    HashedPassword(salt, hash)
  }
}

case class Salt(value: Array[Byte]) {
  def toBase64: String =
    Base64.getEncoder.encodeToString(value)
}

object Salt {
  def fromBase64(value: String): Option[Salt] =
    Try(Base64.getDecoder.decode(value)).toOption.map(Salt(_))

  def randomBytes(bytes: Int): Array[Byte] =
    Array.fill(bytes)((scala.util.Random.nextInt(256) - 128).toByte)

  def randomSalt(bytes: Int = 64): Salt =
    Salt(randomBytes(bytes))
}

case class Hash(value: Array[Byte]) {
  def toBase64: String =
    Base64.getEncoder.encodeToString(value)
}
object Hash {
  def fromBase64(value: String): Option[Hash] =
    Try(Base64.getDecoder.decode(value)).toOption.map(Hash(_))
}
