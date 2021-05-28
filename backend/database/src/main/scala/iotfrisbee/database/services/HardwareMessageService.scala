package iotfrisbee.database.services

import scala.concurrent.ExecutionContext
import cats.effect.Async
import cats.implicits._
import iotfrisbee.database.catalog.HardwareMessageCatalog.{
  HardwareMessageRow,
  HardwareMessageTable,
  toDomain => hardwareMessageToDomain,
}
import iotfrisbee.database.driver.DatabaseDriverOps._
import iotfrisbee.database.driver.DatabaseOutcome.DatabaseResult
import iotfrisbee.domain.{HardwareId, HardwareMessage, HardwareMessageId}

class HardwareMessageService[F[_]: Async](
  val hardwareMessageTable: HardwareMessageTable,
)(implicit executionContext: ExecutionContext) {
  import hardwareMessageTable._
  import hardwareMessageTable.dbDriver.profile.api._

  def countHardwareMessage(): F[DatabaseResult[Int]] =
    HardwareMessageQuery.length.result.tryRunDBIO(dbDriver)

  def createHardwareMessage(
    messageType: String,
    message: String,
    hardwareId: HardwareId,
  ): F[DatabaseResult[HardwareMessage]] = {
    val row = HardwareMessageRow(messageType = messageType, message = message, hardwareId = hardwareId.value)
    (HardwareMessageQuery += row)
      .tryRunDBIO(dbDriver)
      .map(_.map(_ => hardwareMessageToDomain(row)))
  }

  def getHardwareMessage(id: HardwareMessageId): F[DatabaseResult[Option[HardwareMessage]]] =
    HardwareMessageQuery
      .filter(_.uuid === id.value)
      .result
      .headOption
      .map(_.map(hardwareMessageToDomain))
      .tryRunDBIO(dbDriver)

  def getHardwareMessages: F[DatabaseResult[Seq[HardwareMessage]]] =
    HardwareMessageQuery.result
      .map(_.map(hardwareMessageToDomain))
      .tryRunDBIO(dbDriver)

}
