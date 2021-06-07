package iotfrisbee.web.ioControls

import scala.concurrent.Future
import cats.effect.IO
import play.api.mvc.{Result, Codec => PlayCodec}
import play.api.http.{ContentTypeOf, Writeable}
import play.api.http.ContentTypes.JSON
import play.api.mvc.Results.Status
import io.circe.{Json, Decoder => CirceDecoder, Encoder => CirceEncoder}
import iotfrisbee.protocol.WebResult
import iotfrisbee.protocol.WebResult._

object PipelineOps {
  implicit class RichFutureAction[A](f: Future[A]) {
    implicit def asIO: IO[A] = IO.fromFuture(IO(f))
  }

  implicit val contentTypeOfCirceJson: ContentTypeOf[Json] =
    ContentTypeOf[io.circe.Json](Some(JSON))

  implicit def writeableOfCirceJson(implicit codec: PlayCodec): Writeable[Json] =
    Writeable(obj => codec.encode(obj.noSpaces))

  implicit class RichPipelineWebResult[A: CirceEncoder: CirceDecoder](webResult: WebResult[A]) {
    def withHttpStatus(statusCode: Int): Result = Status(statusCode)(webResult.toJsonString).as(JSON)
  }

  implicit class RichPipelineSuccess[A: CirceEncoder: CirceDecoder](success: Success[A]) {
    def withHttpStatus(statusCode: Int): Result = Status(statusCode)(success.toJsonString).as(JSON)
  }

  implicit class RichPipelineFailure[A: CirceEncoder: CirceDecoder](failure: Failure[A]) {
    def withHttpStatus(statusCode: Int): Result = Status(statusCode)(failure.toJsonString).as(JSON)
  }
}
