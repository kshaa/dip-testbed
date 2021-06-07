package iotfrisbee.database.driver

object DatabaseOutcome {
  case class DatabaseError(value: Throwable) extends AnyVal {
    def message: String = value.getMessage
  }

  type DatabaseResult[A] = Either[DatabaseError, A]
}
