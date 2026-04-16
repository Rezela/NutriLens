工作负载身份联合

本文档简要介绍了工作负载身份联合。借助工作负载身份联合，您可以使用联合身份（而非服务账号密钥）为本地或多云工作负载提供对 Google Cloud 资源的访问权限。

您可以将工作负载身份联合与以下工作负载搭配使用：使用 X.509 客户端证书进行身份验证的工作负载、在 Amazon Web Services (AWS) 或 Azure 上运行的工作负载、在本地 Active Directory 上运行的工作负载、在部署服务（例如 GitHub 和 GitLab）上运行的工作负载，还可以将工作负载身份联合与支持 OpenID Connect (OIDC) 或安全断言标记语言 (SAML) V2.0 的任何身份提供方 (IdP) 搭配使用。

为何选择工作负载身份联合？
在 Google Cloud 外部运行的应用可以使用服务账号密钥来访问 Google Cloud 资源。但是，服务账号密钥是强大的凭据，如果管理不当，则可能会带来安全风险。工作负载身份联合可消除与服务账号密钥相关的维护和安全负担。

借助工作负载身份联合，您可以使用 Identity and Access Management (IAM) 向基于工作负载身份池中的联合身份的主账号授予 IAM 角色。您可以向这些主账号授予特定 Google Cloud 资源的访问权限。这种方法称为“直接访问”。或者，您也可以向服务账号授予访问权限，然后该服务账号便可访问 Google Cloud 资源。此方法称为“服务账号模拟”。

工作负载身份池
工作负载身份池是允许您管理外部身份的实体。

通常，我们建议为需要访问Google Cloud资源的每个非 Google Cloud 环境（例如开发环境、预演环境或生产环境）创建一个新池。

工作负载身份池提供方
工作负载身份池提供方是描述 Google Cloud 与您的 IdP 之间关系的实体，包括：

AWS
Microsoft Entra ID
GitHub
GitLab
Kubernetes 集群
Okta
本地 Active Directory Federation Services (AD FS)
Terraform
工作负载身份联合遵循 OAuth 2.0 令牌交换规范。您可以将 IdP 的凭据提供给 Security Token Service，该服务会验证凭据的身份，然后通过交换返回联合令牌。

具有本地 JWK 的 OIDC 提供方
如需联合没有公共 OIDC 端点的工作负载，您可以直接将 OIDC JSON Web 密钥集 (JWKS) 上传到这个池。如果您在自己的环境中托管 Terraform 或 GitHub Enterprise，或者有一些法规要求不公开公共网址，则这种做法很常见。如需了解详情，请参阅管理 OIDC JWK（可选）。

特性映射
您的外部 IdP 颁发的令牌包含一个或多个属性。一些 IdP 将这些属性称为声明。

Google Security Token Service 令牌也包含一个或多个属性，如下表所示：

属性	说明
google.subject	必需。用户的唯一标识符。此属性在 IAM principal:// 角色绑定中使用，并出现在 Cloud Logging 日志中。该值必须是唯一的，不能超过 127 个字符。
google.groups	可选。身份所属的一组群组。此属性在 IAM principalSet:// 角色绑定中使用，以向群组的所有成员授予访问权限。
attribute.NAME	可选。您最多可以定义 50 个自定义属性，并在 IAM principalSet:// 角色绑定中使用这些属性，以向具有特定属性的所有身份授予访问权限。
属性映射定义如何从外部令牌派生 Google Security Token Service 令牌属性的值。您可以为每个 Google Security Token Service 令牌属性定义属性映射，格式如下：

TARGET_ATTRIBUTE=SOURCE_EXPRESSION

替换以下内容：

TARGET_ATTRIBUTE 是一个 Google Security Token Service 令牌属性
SOURCE_EXPRESSION 是一种通用表达式语言 (CEL) 表达式，用于转换外部 IdP 颁发的令牌中的一个或多个属性
以下列表提供了特性映射示例：

将断言属性 sub 分配给 google.subject：


google.subject=assertion.sub
串联多个断言特性：


google.subject='myprovider::' + assertion.aud + '::' + assertion.sub
将 GUID 值的断言特性 workload_id 映射到名称，并将结果分配给名为 attribute.my_display_name 的自定义特性：


attribute.my_display_name={
  "8bb39bdb-1cc5-4447-b7db-a19e920eb111": "Workload1",
  "55d36609-9bcf-48e0-a366-a3cf19027d2a": "Workload2"
}[assertion.workload_id]
使用 CEL 逻辑运算符和函数，将名为 attribute.environment 的自定义特性设置为 prod 或 test，具体取决于身份的 Amazon 资源名称 (ARN)：



attribute.environment=assertion.arn.contains(":instance-profile/Production") ? "prod" : "test"
使用 extract 函数填充自定义特性 aws_role，该角色使用假设角色的名称，或者假设没有角色使用身份的 ARN。



attribute.aws_role=assertion.arn.contains('assumed-role') ? assertion.arn.extract('{account_arn}assumed-role/') + 'assumed-role/' + assertion.arn.extract('assumed-role/{role_name}/') : assertion.arn
使用 split 函数按指定的分隔符值拆分字符串。例如，如需通过在电子邮件地址属性中的 @ 位置处拆分其值并使用第一个字符串，来提取 username 属性，请使用以下属性映射：


attribute.username=assertion.email.split("@")[0]
join 函数按指定的分隔符值联接字符串列表。例如，如需通过以 . 作为分隔符串联字符串列表来填充自定义属性 department，请使用以下属性映射：


attribute.department=assertion.department.join(".")
使用 X.509 客户端证书时，Google 会提供来自证书属性的默认映射。

对于 AWS，Google 提供了可涵盖大多数常见场景的默认映射。您还可以提供自定义映射。

对于 OIDC 提供商，您需要提供映射。如需构建映射，请参阅提供商的文档，查看其凭据的特性列表。

如需了解详情，请参阅 attributeMapping 字段的 API 文档。

特性条件
特性条件是可以检查断言特性和目标特性的 CEL 表达式。如果给定凭据的属性条件判定结果为 true，则系统会接受凭据。否则，凭据会被拒绝。

您可以使用特性条件来限制哪些身份可以使用工作负载身份池进行身份验证。

特性条件在如下情况下非常有用：

如果您的工作负载使用向公众提供的 IdP，您可以限制访问权限，以便只有您选择的身份才有权访问您的工作负载身份池。

如果您将一个 IdP 用于多个云平台，则可以防止将预期用于其他平台的凭据用于 Google Cloud，反之亦然。这有助于避免混淆代理问题。

工作负载身份池提供方的属性条件可以使用 assertion 关键字，该关键字是指一个映射，代表由 IdP 颁发的身份验证凭据。您可以使用点表示法来访问该映射的值。例如，AWS 凭据包含 arn 值，您可以以 assertion.arn 的形式访问该值。此外，特性条件可以使用提供商的特性映射中定义的任何特性。

以下示例仅接受来自具有特定 AWS 角色的身份的请求：



attribute.aws_role == "ROLE_MAPPING"
如需了解详情，请参阅 attributeCondition 字段的 API 文档。

访问权限管理
令牌交换流程会返回联合访问令牌。您可以使用此联合访问令牌来代表主账号身份为工作负载授予对 Google Cloud 资源的访问权限，并获取短期有效的 OAuth 2.0 访问令牌。

您可以使用此访问令牌来提供 IAM 访问权限。

我们建议您使用工作负载身份联合来提供直接对 Google Cloud 资源的访问权限。虽然大多数 Google Cloud API 都支持工作负载身份联合，但某些 API 存在限制。或者，您也可以使用服务账号模拟。

短期有效的访问令牌可让您调用资源或服务账号有权访问的任何 Google Cloud API。

直接资源访问权限
您可以通过直接资源访问权限，使用特定于资源的角色，向外部身份授予直接对 Google Cloud 资源的访问权限。

替代方法：服务账号模拟
除了提供直接资源访问权限，您还可以使用服务账号模拟。

注意：向外部身份授予角色时，请使用完全限定的资源名称，并使用您的项目编号，而不是项目 ID。
您必须向服务账号授予 Workload Identity User 角色 (roles/iam.workloadIdentityUser)。

主账号范围和安全性
您可以使用主账号类型向主账号或其子集授予访问权限。

警告：虽然您可以向工作负载身份池中的所有身份授予访问权限，但这样做可能会产生风险。我们建议您使用属性和条件来限制访问权限。
主账号类型
下表介绍了如何将主账号定义为个人和身份群组：

身份	标识符格式
单一身份	principal://iam.googleapis.com/projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/POOL_ID/subject/SUBJECT_ATTRIBUTE_VALUE
群组中的所有身份	principalSet://iam.googleapis.com/projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/POOL_ID/group/GROUP_ID
具有特定特性值的所有身份	principalSet://iam.googleapis.com/projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/POOL_ID/attribute.ATTRIBUTE_NAME/ATTRIBUTE_VALUE
后续步骤
使用工作负载身份联合，让您的工作负载访问来自 AWS 或 Azure、X.509 证书、Active Directory、部署流水线或者 OIDC 或 SAML 提供方的资源。

了解如何使用 Google Cloud CLI 或 REST API 管理工作负载身份池。