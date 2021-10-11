package iotfrisbee.web.controllers

import iotfrisbee.database.driver.DatabaseOutcome.DatabaseException
import iotfrisbee.protocol.WebResult.Failure
import iotfrisbee.web.ioControls.PipelineOps._
import play.api.http.Status.INTERNAL_SERVER_ERROR
import play.api.mvc.Result

trait ResultsController[F[_]] {
  def databaseErrorResult(error: DatabaseException): Result =
    Failure(error.message).withHttpStatus(INTERNAL_SERVER_ERROR)
}


