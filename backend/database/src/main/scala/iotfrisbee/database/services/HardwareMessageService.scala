package iotfrisbee.database.services

import scala.concurrent.ExecutionContext
import cats.effect.Async
import cats.implicits._
import io.circe.Json
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
  import hardwareMessageTable.dbDriver.profile.api._
  import hardwareMessageTable._

  def countHardwareMessage(): F[DatabaseResult[Int]] =
    HardwareMessageQuery.length.result.tryRunDBIO(dbDriver)

  def createHardwareMessage(
    messageType: String,
    message: Json,
    hardwareId: HardwareId,
  ): F[DatabaseResult[HardwareMessage]] = {
    val row = HardwareMessageRow(messageType = messageType, message = message.noSpaces, hardwareId = hardwareId.value)
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

  def getHardwareMessages(hardwareId: Option[HardwareId]): F[DatabaseResult[Seq[HardwareMessage]]] =
    HardwareMessageQuery
      .filterOpt(hardwareId)(_.hardwareUuid === _.value)
      .result
      .map(_.map(hardwareMessageToDomain))
      .tryRunDBIO(dbDriver)

}
