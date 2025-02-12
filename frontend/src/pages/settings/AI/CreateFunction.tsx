import { Loader } from '@/components/common/Loader'
import FunctionForm from '@/components/feature/settings/ai/functions/FunctionForm'
import { ErrorBanner } from '@/components/layout/AlertBanner/ErrorBanner'
import PageContainer from '@/components/layout/Settings/PageContainer'
import SettingsContentContainer from '@/components/layout/Settings/SettingsContentContainer'
import SettingsPageHeader from '@/components/layout/Settings/SettingsPageHeader'
import { RavenAIFunction } from '@/types/RavenAI/RavenAIFunction'
import { Button } from '@radix-ui/themes'
import { useFrappeCreateDoc } from 'frappe-react-sdk'
import { FormProvider, useForm } from 'react-hook-form'
import { useNavigate } from 'react-router-dom'

const CreateFunction = () => {

    const { createDoc, loading, error } = useFrappeCreateDoc<RavenAIFunction>()

    const methods = useForm<RavenAIFunction>({
        disabled: loading,
        defaultValues: {
            params: {
                type: 'object',
                properties: {},
            }
        }
    })

    const navigate = useNavigate()


    const onSubmit = (data: RavenAIFunction) => {
        createDoc("Raven AI Function", data)
            .then((doc) => {
                navigate(`../${doc.name}`)
            })
    }

    return (
        <PageContainer>
            <form onSubmit={methods.handleSubmit(onSubmit)}>
                <FormProvider {...methods}>
                    <SettingsContentContainer>
                        <SettingsPageHeader
                            title='Create a Function'
                            actions={<Button type='submit' disabled={loading}>
                                {loading && <Loader />}
                                {loading ? "Creating" : "Create"}
                            </Button>}
                            breadcrumbs={[{ label: 'Functions', href: '../' }, { label: 'New Function', href: '' }]}
                        />
                        <ErrorBanner error={error} />
                        <FunctionForm />
                    </SettingsContentContainer>
                </FormProvider>
            </form>
        </PageContainer>
    )
}

export const Component = CreateFunction