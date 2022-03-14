package diptestbed.web.control

import diptestbed.database.driver.DatabaseOutcome.DatabaseException
import diptestbed.protocol.WebResult.Failure
import diptestbed.web.ioControls.PipelineOps._
import play.api.http.Status.{BAD_REQUEST, INTERNAL_SERVER_ERROR, UNAUTHORIZED}
import play.api.mvc.Result

trait ResultsController[F[_]] {
  def databaseErrorResult(error: DatabaseException): Result =
    Failure(error.message).withHttpStatus(INTERNAL_SERVER_ERROR)

  def unknownIdErrorResult: Result =
    Failure(s"Entity with such id does not exist").withHttpStatus(BAD_REQUEST)

  def permissionErrorResult(permission: String): Result =
    Failure(s"Missing permissions: ${permission}").withHttpStatus(UNAUTHORIZED)

}
