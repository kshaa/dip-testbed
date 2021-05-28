package iotfrisbee.database.services

import scala.concurrent.ExecutionContext
import cats.effect.Async
import cats.implicits._
import iotfrisbee.database.catalog.HardwareCatalog.{HardwareRow, HardwareTable, toDomain => hardwareToDomain}
import iotfrisbee.database.driver.DatabaseDriverOps._
import iotfrisbee.database.driver.DatabaseOutcome.DatabaseResult
import iotfrisbee.domain.{Hardware, HardwareId, UserId}

class HardwareService[F[_]: Async](
  val hardwareTable: HardwareTable,
)(implicit executionContext: ExecutionContext) {
  import hardwareTable.dbDriver.profile.api._
  import hardwareTable._

  def countHardware(): F[DatabaseResult[Int]] =
    HardwareQuery.length.result.tryRunDBIO(dbDriver)

  def createHardware(
    name: String,
    ownerId: UserId,
  ): F[DatabaseResult[Hardware]] = {
    val row = HardwareRow(name = name, ownerId = ownerId.value)
    (HardwareQuery += row)
      .tryRunDBIO(dbDriver)
      .map(_.map(_ => hardwareToDomain(row)))
  }

  def getHardware(id: HardwareId): F[DatabaseResult[Option[Hardware]]] =
    HardwareQuery
      .filter(_.uuid === id.value)
      .result
      .headOption
      .map(_.map(hardwareToDomain))
      .tryRunDBIO(dbDriver)

  def getHardwares: F[DatabaseResult[Seq[Hardware]]] =
    HardwareQuery.result
      .map(_.map(hardwareToDomain))
      .tryRunDBIO(dbDriver)

}
