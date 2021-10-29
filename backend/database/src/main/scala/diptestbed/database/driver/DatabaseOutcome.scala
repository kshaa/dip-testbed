package diptestbed.database.driver

object DatabaseOutcome {
  case class DatabaseException(cause: Throwable) extends Exception(cause) {
    def message: String = cause.getMessage
  }

  type DatabaseResult[A] = Either[DatabaseException, A]
}
